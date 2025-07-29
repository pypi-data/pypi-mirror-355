# Singleton Mask File

## clean

> This command cleans the build artifacts

```bash
rm -rf dist/
```

## bump (patch_version)

> Bump the version of the local project specifying the patch level: `minor`, `major`, `patch`

```bash
bump2version ${patch_version} --allow-dirty
```

## build

> This command builds the project via uv

```bash
uv build
```

## test

> This command runs the tests using nox

```bash
nox -s
```

