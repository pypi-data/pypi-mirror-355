class ChatmcpCli < Formula
  include Language::Python::Virtualenv

  desc "ChatMCP CLI - AI pair programming with MCP server integration"
  homepage "https://github.com/soulful-ai/platforma"
  url "https://files.pythonhosted.org/packages/b0/30/80c4fb4c893c3e85f9393584f603b764f2d5fe02608ed69ed35fe27eb99d/chatmcp_cli-0.1.0.tar.gz"
  sha256 "3ef6f0dbb2dc3617ffa098a99d54cdb10e1d669bb1cc8c3858890982cc69e1b6"
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "usage:", shell_output("#{bin}/chatmcp --help")
    assert_match "usage:", shell_output("#{bin}/aider --help")
  end
end