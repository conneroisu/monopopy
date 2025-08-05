{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = inputs @ {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachSystem ["x86_64-linux" "aarch64-linux" "aarch64-darwin"] (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        # Platform-specific packages
        linuxPackages = pkgs.lib.optionals pkgs.stdenv.isLinux [
          pkgs.libGL
          pkgs.mesa
          pkgs.xorg.libX11
          pkgs.xorg.libXrandr
          pkgs.xorg.libXinerama
          pkgs.xorg.libXcursor
          pkgs.xorg.libXi
        ];

        darwinPackages = pkgs.lib.optionals pkgs.stdenv.isDarwin [
          pkgs.libiconv
          pkgs.darwin.apple_sdk.frameworks.CoreFoundation
          pkgs.darwin.apple_sdk.frameworks.CoreServices
          pkgs.darwin.apple_sdk.frameworks.Foundation
          pkgs.darwin.apple_sdk.frameworks.Security
          pkgs.darwin.apple_sdk.frameworks.SystemConfiguration
        ];

        rooted = exec:
          builtins.concatStringsSep "\n"
          [
            ''REPO_ROOT="$(git rev-parse --show-toplevel)"''
            exec
          ];

        scripts = {
          dx = {
            exec = rooted ''$EDITOR "$REPO_ROOT"/flake.nix'';
            description = "Edit flake.nix";
          };
          px = {
            exec = rooted ''$EDITOR "$REPO_ROOT"/pyproject.toml'';
            description = "Edit pyproject.toml";
          };
          clean = {
            exec = ''git clean -fdx'';
            description = "Clean project";
          };
          lint-python = {
            exec = rooted ''
              cd "$REPO_ROOT"
              ruff check .
              ruff format --check .
              mypy . || true
            '';
            deps = with pkgs; [ruff mypy];
            description = "Lint Python code";
          };
          lint = {
            exec = rooted ''
              lint-python
              statix check "$REPO_ROOT"
              deadnix "$REPO_ROOT"/flake.nix
              nix flake check
            '';
            deps = with pkgs; [statix deadnix ruff mypy];
            description = "Run all linting steps";
          };
          build-nix = {
            exec = rooted ''cd "$REPO_ROOT" && nix build'';
            deps = [];
            description = "Build with Nix";
          };
          format = {
            exec = rooted ''
              cd "$REPO_ROOT"
              ruff format .
              alejandra "$REPO_ROOT"/flake.nix
            '';
            deps = with pkgs; [alejandra ruff];
            description = "Format all code";
          };
        };

        scriptPackages =
          pkgs.lib.mapAttrs
          (
            name: script:
              pkgs.writeShellApplication {
                inherit name;
                text = script.exec;
                runtimeInputs = script.deps or [];
                runtimeEnv = script.env or {};
              }
          )
          scripts;
      in {
        devShells = let
          shellHook = ''
            echo "🐍 Python development environment"
            echo "Available commands:"
            ${pkgs.lib.concatStringsSep "\n" (
              pkgs.lib.mapAttrsToList (name: script: ''echo "  ${name} - ${script.description}"'') scripts
            )}
            echo ""
          '';

          env =
            {
              DEV = "1";
              LOCAL = "1";
            }
            // pkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
            }
            // pkgs.lib.optionalAttrs pkgs.stdenv.isDarwin {
              DYLD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
            };

          corePackages = [
            # Nix development tools
            pkgs.alejandra
            pkgs.nixd
            pkgs.nil
            pkgs.statix
            pkgs.deadnix
          ];

          pythonPackages = [
            pkgs.python312
            pkgs.uv
            pkgs.ruff
            pkgs.mypy
          ];


          systemPackages = [
            pkgs.pkg-config
            pkgs.protobuf
            pkgs.openssl
            pkgs.opencv4
          ];

          shell-packages =
            corePackages
            ++ pythonPackages
            ++ systemPackages
            ++ linuxPackages
            ++ darwinPackages
            ++ builtins.attrValues scriptPackages;
        in {
          default = pkgs.mkShell {
            inherit shellHook env;
            packages = shell-packages;
          };
        };

        packages = {
          default = pkgs.stdenv.mkDerivation {
            pname = "monopopy";
            version = "0.1.0";
            
            src = ./.;
            
            buildInputs = [ pkgs.python312 pkgs.python312Packages.rich ];
            
            installPhase = ''
              mkdir -p $out/bin
              mkdir -p $out/share/monopopy
              
              # Debug: List files in source directory
              echo "Source files:"
              ls -la
              
              # Copy source files - handle the case where files might not exist
              if [ -f main.py ]; then
                cp main.py $out/share/monopopy/
              fi
              if [ -f test_game.py ]; then
                cp test_game.py $out/share/monopopy/
              fi
              if [ -f README.md ]; then
                cp README.md $out/share/monopopy/
              fi
              if [ -f LICENSE ]; then
                cp LICENSE $out/share/monopopy/
              fi
              
              # Create executable script
              cat > $out/bin/monopopy << EOF
              #!/usr/bin/env bash
              export PYTHONPATH="\$PYTHONPATH:${pkgs.python312Packages.rich}/lib/python3.12/site-packages"
              exec ${pkgs.python312}/bin/python $out/share/monopopy/main.py "\$@"
              EOF
              
              # Create monopoly alias
              cat > $out/bin/monopoly << EOF
              #!/usr/bin/env bash
              export PYTHONPATH="\$PYTHONPATH:${pkgs.python312Packages.rich}/lib/python3.12/site-packages"
              exec ${pkgs.python312}/bin/python $out/share/monopopy/main.py "\$@"
              EOF
              
              chmod +x $out/bin/monopopy
              chmod +x $out/bin/monopoly
            '';
            
            meta = with pkgs.lib; {
              description = "A complete Monopoly game implementation with rich TUI interface";
              homepage = "https://github.com/user/monopopy";
              license = licenses.mit;
              maintainers = [ ];
              platforms = platforms.unix;
            };
          };
          
          monopopy = pkgs.stdenv.mkDerivation {
            pname = "monopopy";
            version = "0.1.0";
            
            src = ./.;
            
            buildInputs = [ pkgs.python312 pkgs.python312Packages.rich ];
            
            installPhase = ''
              mkdir -p $out/bin
              mkdir -p $out/share/monopopy
              
              # Debug: List files in source directory
              echo "Source files:"
              ls -la
              
              # Copy source files - handle the case where files might not exist
              if [ -f main.py ]; then
                cp main.py $out/share/monopopy/
              fi
              if [ -f test_game.py ]; then
                cp test_game.py $out/share/monopopy/
              fi
              if [ -f README.md ]; then
                cp README.md $out/share/monopopy/
              fi
              if [ -f LICENSE ]; then
                cp LICENSE $out/share/monopopy/
              fi
              
              # Create executable script
              cat > $out/bin/monopopy << EOF
              #!/usr/bin/env bash
              export PYTHONPATH="\$PYTHONPATH:${pkgs.python312Packages.rich}/lib/python3.12/site-packages"
              exec ${pkgs.python312}/bin/python $out/share/monopopy/main.py "\$@"
              EOF
              
              # Create monopoly alias
              cat > $out/bin/monopoly << EOF
              #!/usr/bin/env bash
              export PYTHONPATH="\$PYTHONPATH:${pkgs.python312Packages.rich}/lib/python3.12/site-packages"
              exec ${pkgs.python312}/bin/python $out/share/monopopy/main.py "\$@"
              EOF
              
              chmod +x $out/bin/monopopy
              chmod +x $out/bin/monopoly
            '';
            
            meta = with pkgs.lib; {
              description = "A complete Monopoly game implementation with rich TUI interface";
              homepage = "https://github.com/user/monopoly";
              license = licenses.mit;
              maintainers = [ ];
              platforms = platforms.unix;
            };
          };
        };
      }
    );
}
