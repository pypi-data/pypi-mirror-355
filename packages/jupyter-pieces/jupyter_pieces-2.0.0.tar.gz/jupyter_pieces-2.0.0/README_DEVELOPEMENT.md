# This is the development readme for this plugin

### Use this as a resource for setting up a development environment for this plugin.

### How to set up the development environment

_this follows this example:_ https://jupyterlab.readthedocs.io/en/stable/extension/extension_tutorial.html#set-up-a-development-environment

1. install conda, pip, and jupyterlab
2. set up a conda environment for development
3. clone this project
4. activate the conda environment you just created
5. run `jlpm install`, jlpm is the package manager we need to be using for this extension
6. Install rust: https://www.rust-lang.org/tools/install. 'Cargo' is used during install pip script.
7. from the root dir of this project, with your conda env activated, run `pip install -ve .`
8. create a symlink for fast reloading by doing: `jupyter labextension develop --overwrite .` again with the conda env activated and from the root dir of the project
9. start jupyterlab
10. in a different terminal shell, run `jlpm run watch` in order to start an incremental watch compiler.
11. happy coding!

If you have troubles with installing pip packages within your conda env, you can try using `pip list` to see if you have incorrect packages and remove the bad ones with `pip uninstall {package}`, or simply create a new conda environment and start fresh.

### Trigger a Release

- Staging releases are triggered on a push to main (submit and merge a pr)
- Run `npm run {patch | minor | major}-release` in order to automatically generate a changelog, tag, and bump versions in repo
- Publish release in Github: https://github.com/pieces-app/plugin_jupyter/releases/new, add tag and title with version name, generate release notes (no need to upload artifacts)
