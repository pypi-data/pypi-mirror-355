{
  description = "My nix dev environment for uv mainly";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, flake-utils, nixpkgs }@inputs :
    flake-utils.lib.eachDefaultSystem (system:
    let
        pkgs =
        import nixpkgs {
            inherit system;
            config.allowUnfree = true;
        };
    in
    {
      devShells = { 

        default = (
            let 
                buildInputs = [
                    pkgs.zlib #Numpy
                    pkgs.libxcrypt # In any case
                    pkgs.libxcrypt-legacy # For Python3.7
                    pkgs.stdenv.cc.cc.lib
                    pkgs.sox
                    pkgs.libsndfile
                    pkgs.ffmpeg_6-headless
                ];
            in 
        pkgs.buildFHSEnv {
         name = "uv-env";
         targetPkgs = pkgs:
           [
             pkgs.uv
             pkgs.which
             pkgs.bashInteractive
           ];
         profile = ''
         export LD_LIBRARY_PATH="${
            with pkgs;
            lib.makeLibraryPath buildInputs
            }:$LD_LIBRARY_PATH";
         echo "This shell has uv activated at ${pkgs.uv}"
         '';
         runScript = "bash";
       }).env;

      python = pkgs.mkShell {
        name = "pythonshell";
        buildInputs = with pkgs; [
          python310
          python310Packages.venvShellHook
        ];
        shellHook = ''
          echo "Python development shell activated!"
        '';
      };
      };
    });
}
