# CNHAAI Development Environment (Nix)
#
# Usage:
#   nix-shell                    # Enter development shell
#   nix-shell --run "pytest"     # Run command directly
#   nix develop                  # Using flakes (nix 2.4+)

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Python version
  pythonVersion = "python311";

  # Build inputs (packages available in shell)
  buildInputs = with pkgs; [
    # Python and essentials
    python311
    python311Packages.pip
    python311Packages.venv

    # Development tools
    (python311Packages.black.overrideAttrs (old: {
      # Keep existing configure flags, add any customizations
    }))
    (python311Packages.mypy.overrideAttrs (old: {
      # Keep existing configure flags, add any customizations
    }))
    python311Packages.pytest
    python311Packages.pytest-cov
    python311Packages.flake8

    # Optional: Additional useful tools
    git
    nixfmt
  ];

  # Shell environment variables
  shellHook = ''
    export PYTHONPATH="${srcPath}:$PYTHONPATH"
    export PYTHONDONTWRITEBYTECODE=1

    # Print welcome message
    echo "CNHAAI Development Environment"
    echo "Python: $(python --version)"
    echo ""
    echo "Available commands:"
    echo "  pytest       - Run tests"
    echo "  black        - Format code"
    echo "  mypy         - Type check"
    echo "  flake8       - Lint code"
  '';

  # Extra inputs for nix-shell (non-build inputs)
  nativeBuildInputs = with pkgs; [
    # Tools needed during build/development but not in runtime
  ];

  # RUNTIME dependencies (packages available to scripts)
  passAsFile = [ "blackExtraArgs" ];
}

# Alternative: Flake-based development shell
#
# Create a flake.nix file with:
#
# {
#   inputs = {
#     nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
#   };
#
#   outputs = { self, nixpkgs }:
#     let
#       pkgs = nixpkgs.legacyPackages.x86_64-linux;
#     in
#     {
#       devShells.x86_64-linux.default = pkgs.mkShell {
#         buildInputs = with pkgs; [
#           python311
#           python311Packages.black
#           python311Packages.mypy
#           python311Packages.pytest
#           python311Packages.pytest-cov
#           python311Packages.flake8
#         ];
#       };
#     };
# }
