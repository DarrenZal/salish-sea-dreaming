# Salish Sea Dreaming

AI-assisted visual art exploring the Salish Sea ecosystem through TouchDesigner.

This project uses AI (Claude) to help create and control particle-based visualizations of marine life - from plankton to orcas.

## Live Demo

**[Try the Web Prototype](https://darrenzal.github.io/salish-sea-dreaming/)** - Move slowly. Be still. The sea reveals itself to those who wait.

## What's Inside

- `web/` - Three.js web prototype (runs in browser, no install needed)
- `examples/FishSchool.toe` - TouchDesigner point cloud fish school visualization

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

## Web Prototype

The `web/` directory contains a Three.js prototype for rapid iteration:

```bash
cd web
npm install
npm run dev
```

This runs at `http://localhost:3000`. Changes appear instantly (hot reload).

**Why both web and TouchDesigner?**
- **Web (Three.js)**: Fast prototyping, easy sharing via URL, great for AI-assisted development
- **TouchDesigner**: Production installation, projection mapping, Kinect, audio integration

We prototype ideas in the browser, then port the good ones to TouchDesigner for the gallery.

## For Developers / Advanced Users

If you're using Claude Code or want more control, see the full [TouchDesigner MCP documentation](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md).

**Claude Code setup:**
```bash
claude mcp add -s user touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

## About This Project

> *"We are the Salish Sea, dreaming itself awake."*

Salish Sea Dreaming is an evolving art + technology exploration, working toward an **Interactive AI Dreaming Mind** installation for the [Salt Spring Spring Art Show](https://saltspringarts.com/spring-art-show/) (April 2026).

The project sits at the intersection of:
- **Interactive art & immersive media** - TouchDesigner, projection mapping, presence detection
- **Bioregional consciousness** - Technology as a "listening interface" to help humans tune into living systems
- **Indigenous worldviews** - Informed by Indigenomics and relational economics
- **Data poetics** - Translating ecological data into felt, responsive experiences

### The Vision

Not humans looking at nature through technology, but the Salish Sea using technology (and us) to perceive itself.

### Collaborators

- [Pravin Pillay / MOVE37XR](https://www.move37xr.org/) - Creative direction, immersive media
- [Briony Penn](https://brionypenn.com/) - Naturalist illustration, ecological storytelling
- [Carol Anne Hilton / Indigenomics](https://indigenomics.com/) - Indigenous economic worldviews
- Darren Zal - Knowledge systems, data infrastructure
- Shawn - Creative technology, AI systems

### Related Resources

- [Mind Map (Coggle)](https://coggle.it/diagram/aW01lIKXUtVgH4cW/t/wen%2Cn%C3%A1%2Cnec)
- [Shared Drive](https://drive.google.com/drive/folders/1eWuiMKqALHh8SWBjMRRCMu5wrGoK8oEO)

## Credits

- Built with [TouchDesigner MCP](https://github.com/8beeeaaat/touchdesigner-mcp) by [@8beeeaaat](https://github.com/8beeeaaat)
- Created with assistance from Claude (Anthropic)

## License

MIT
