# Salish Sea Dreaming

AI-assisted visual art exploring the Salish Sea ecosystem through TouchDesigner.

This project uses AI (Claude) to help create and control particle-based visualizations of marine life - from plankton to orcas.

## What's Inside

- `examples/FishSchool.toe` - A point cloud fish school visualization

## Quick Start (For Artists)

### What You Need

1. **TouchDesigner** (free version works) - [Download here](https://derivative.ca/download)
2. **Claude Desktop** or **Claude Code** - For AI assistance

### Setup (5 minutes)

#### Step 1: Set up TouchDesigner

1. Download the TouchDesigner component from the [touchdesigner-mcp releases](https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest):
   - Download `touchdesigner-mcp-td.zip`
   - Extract it somewhere you'll remember

2. Open TouchDesigner and your project (or create a new one)

3. Drag `mcp_webserver_base.tox` from the extracted folder into your TouchDesigner project
   - Place it at `/project1/mcp_webserver_base`
   - **Important:** Keep the entire extracted folder intact - don't move files around

4. Verify it's working: Press `Alt+T` to open Textport - you should see a message about the server starting

#### Step 2: Connect Claude Desktop

**Easiest method** (Claude Desktop only):
1. Download `touchdesigner-mcp.mcpb` from the [same releases page](https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest)
2. Double-click the `.mcpb` file - it auto-installs in Claude Desktop
3. Restart Claude Desktop

**That's it!** Now you can ask Claude to help you create and modify TouchDesigner projects.

### Using It

With TouchDesigner running and the MCP component active:

1. Open Claude Desktop
2. Ask Claude things like:
   - "Create a particle system with 1000 points"
   - "Make the particles blue and increase their size"
   - "Add a noise effect to animate the particles"
   - "Show me what nodes exist in my project"

Claude can see and modify your TouchDesigner project in real-time.

## For Developers / Advanced Users

If you're using Claude Code or want more control, see the full [TouchDesigner MCP documentation](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md).

**Claude Code setup:**
```bash
claude mcp add -s user touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

## About This Project

This project explores the Salish Sea ecosystem through generative art:
- **Plankton** - The foundation of the food web
- **Herring** - Small schooling fish
- **Salmon** - The iconic Pacific salmon
- **Orcas** - The apex predators, Southern Resident Killer Whales

## Credits

- Built with [TouchDesigner MCP](https://github.com/8beeeaaat/touchdesigner-mcp) by [@8beeeaaat](https://github.com/8beeeaaat)
- Created with assistance from Claude (Anthropic)

## License

MIT
