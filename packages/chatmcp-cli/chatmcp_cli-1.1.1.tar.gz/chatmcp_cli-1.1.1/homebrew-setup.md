# Homebrew Formula for ChatMCP CLI

## Formula Ready
Created `chatmcp-cli.rb` with:
- **Package**: `chatmcp-cli` v0.1.0
- **SHA256**: `3ef6f0dbb2dc3617ffa098a99d54cdb10e1d669bb1cc8c3858890982cc69e1b6`
- **URL**: https://files.pythonhosted.org/packages/b0/30/80c4fb4c893c3e85f9393584f603b764f2d5fe02608ed69ed35fe27eb99d/chatmcp_cli-0.1.0.tar.gz

## Next Steps (on macOS/Linux with Homebrew)

### 1. Test Formula Locally
```bash
# Test the formula
brew install --build-from-source ./chatmcp-cli.rb
brew test chatmcp-cli

# Test commands work
chatmcp --help
aider --help

# Uninstall test
brew uninstall chatmcp-cli
```

### 2. Submit to Homebrew Core
```bash
# Fork and clone homebrew-core
git clone https://github.com/YOUR_USERNAME/homebrew-core.git
cd homebrew-core

# Add formula
cp ../chatmcp-cli.rb Formula/

# Create commit
git add Formula/chatmcp-cli.rb
git commit -m "chatmcp-cli: new formula

ChatMCP CLI - AI pair programming with MCP server integration"

# Push and create PR
git push origin main
```

### 3. Alternative: Personal Tap
For faster approval, create a personal tap:

```bash
# Create tap repository
gh repo create homebrew-tap --public

# Clone and add formula
git clone https://github.com/YOUR_USERNAME/homebrew-tap.git
cd homebrew-tap
mkdir -p Formula
cp ../chatmcp-cli.rb Formula/
git add Formula/chatmcp-cli.rb
git commit -m "Add chatmcp-cli formula"
git push origin main

# Users can then install with:
brew tap YOUR_USERNAME/tap
brew install YOUR_USERNAME/tap/chatmcp-cli
```

## Formula Requirements Met
✅ Python virtualenv support  
✅ Proper dependencies (python@3.12)  
✅ Test cases for both commands  
✅ Correct licensing (Apache-2.0)  
✅ Valid homepage and description  
✅ Verified SHA256 hash  

Ready for Homebrew submission!