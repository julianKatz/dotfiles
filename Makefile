brew:
	brew update
	./brew-repair.sh
	brew bundle --file=homebrew/Brewfile
	brew upgrade


stow:
	./stow-all.sh

default-shell:
	@ZSH_PATH=$$(which zsh); \
	CURRENT_SHELL=$$(dscl . -read ~/ UserShell | awk '{print $$2}'); \
	if [ "$$CURRENT_SHELL" = "$$ZSH_PATH" ]; then \
		echo "✅ Zsh is already the default shell."; \
	else \
		if ! grep -q "$$ZSH_PATH" /etc/shells; then \
			echo "➕ Adding $$ZSH_PATH to /etc/shells"; \
			echo "$$ZSH_PATH" | sudo tee -a /etc/shells; \
		fi; \
		echo "🔁 Changing default shell to $$ZSH_PATH"; \
		chsh -s "$$ZSH_PATH"; \
	fi

setup: brew default-shell zinit stow

zinit:
	@echo "🔍 Checking for zinit..."
	@if [ ! -d "$$HOME/.zinit" ]; then \
		echo "📥 Installing zinit..."; \
		sh -c "$$(curl -fsSL https://git.io/zinit-install)"; \
	else \
		echo "✅ zinit already installed."; \
	fi

.PHONY: \
	stow \
	brew \
	default-shell \
	zinit
