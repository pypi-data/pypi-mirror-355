let
    pkgs = import (builtins.fetchTarball {
        url = "https://github.com/NixOS/nixpkgs/archive/f780db4505588b541fd472cd1c7ed9cbd9c4b469.tar.gz";
    }) {};
    python = pkgs.python312;
    avro-validator = python.pkgs.buildPythonPackage (rec {
      pname = "avro_validator";
      version = "1.2.1";
      format = "setuptools";
      src = pkgs.fetchFromGitHub {
        owner = "leocalm";
        repo = pname;
        rev = "refs/tags/${version}";
        hash = "sha256:17lxwy68r6wn3mpz3l7bi3ajg7xibp2sdz94hhjigfkxvz9jyi2f";
      };
      pythonImportsCheck = [ "avro_validator" ];
    });
    highlighter-sdk = python.pkgs.buildPythonPackage (rec {
      pname = "highlighter_sdk";
      version = "2.4.74";
      format = "pyproject";
      buildInputs = [ python.pkgs.hatchling ];
      src = python.pkgs.fetchPypi {
        inherit pname version;
        hash = "sha256-rj2RrHXqcbPyr8y8CMBxmq2zAuZFLpXDuD6fByCTces=";
      };
      postPatch = ''
        substituteInPlace pyproject.toml \
          --replace-fail 'packages = ["src/highlighter", "src/aiko_services"]' \
                         'packages = ["highlighter", "aiko_services"]'

      '';
      propagatedBuildInputs = with python.pkgs; [
        aiohttp
        fastavro
        boto3
        click
        colorama
        gql
        jupyterlab
        opencv4
        pandas
        pillow
        pooch
        pydantic
        python-magic
        pyyaml
        requests
        requests-toolbelt
        shapely
        tables
        tqdm
        websockets
        requests-toolbelt
        cookiecutter

        # aiko_services is vendored inside highlighter-sdk,
        # these are its dependencies
        asciimatics
        avro
        avro-validator
        paho-mqtt
        pyperclip
        transitions
        wrapt
      ];
      nativeBuildInputs = [ python.pkgs.pythonRelaxDepsHook ];
      pythonRelaxDeps = [
        "boto3"
        "paho-mqtt"
        "pillow"
        "psutil"
        "pydantic"
        "websockets"
        "wrapt"
      ];
      pythonRemoveDeps = [
        "opencv-python"
      ];
      pythonImportsCheck = [ "highlighter" "aiko_services" ];
    });
    pythonEnv = python.withPackages (ps: with ps; [
      numpy ipython magic highlighter-sdk
    ]);
in
pkgs.mkShell {
  buildInputs = [ pythonEnv ];
  shellHook = "export PYTHONPATH=$PWD/src:$PYTHONPATH";
}
