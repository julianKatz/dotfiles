#!/bin/bash

# Force-reinstall casks whose artifacts were deleted outside of Homebrew, e.g.
# dragging an app to the Trash or removing a font in Font Book.  Homebrew still
# records them as installed, but the next `brew upgrade` aborts: uninstalling
# the old version means moving the artifact back into the Caskroom, and it is
# no longer there.  A no-op when everything is where Homebrew left it.

if ! command -v brew > /dev/null; then
  printf "Homebrew not found on path.  Install then try again.\n"
  exit 1
fi

CASKROOM="$(brew --prefix)/Caskroom"
[ -d "$CASKROOM" ] || exit 0

broken=""
for version_dir in "$CASKROOM"/*/*/; do
  for artifact in "$version_dir"*; do
    # Homebrew leaves a symlink in the Caskroom pointing at wherever it moved
    # the artifact.  A dangling one means the artifact is gone.
    if [ -L "$artifact" ] && [ ! -e "$artifact" ]; then
      cask="${version_dir%/*/}"
      broken="$broken ${cask##*/}"
      break
    fi
  done
done

if [ -z "$broken" ]; then
  printf "✅ All casks still have their artifacts.\n"
  exit 0
fi

printf "🔧 Reinstalling casks with missing artifacts:%s\n" "$broken"
# Intentionally unquoted: $broken is a space-separated list of cask names.
# shellcheck disable=SC2086
brew reinstall --cask --force $broken
