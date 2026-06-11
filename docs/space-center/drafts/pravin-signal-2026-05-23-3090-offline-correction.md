Correction on the diagnosis — checked the backups: WireGuard (10.100.0.30) and Tailscale (100.91.172.10) both also fail to ping. Three independent paths dead at once → the 3090 itself looks offline, not just the tunnel service. Power blip, Windows auto-reboot, or hard crash are the likely culprits.

schtasks /run won't fix this — there's no Windows session listening yet. The box needs eyes-on:
1. Check it's powered on
2. If yes but unresponsive → hard power cycle
3. Once it boots, the SSD-SSH-Tunnel task should auto-start on logon

Same no-rush. I'm keeping busy prepping subclip cuts for the Bob Turner scrape and other things that don't need the 3090.
