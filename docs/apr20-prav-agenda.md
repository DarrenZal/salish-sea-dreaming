# Apr 20 — 9:30–10:30 with Prav (simple)

Prav at gallery 9:30. Must catch 11:50 ferry. One hour window.

1. Prav: restart SSH tunnel at 3090 keyboard.
   ```powershell
   schtasks /run /tn "SSD-SSH-Tunnel"
   ```
2. Darren (remote): confirm `ssh windows-desktop-remote` works. Say "I'm in" on Signal.
3. Darren: run the one-command deploy.
   ```powershell
   iex (iwr https://salishseadreaming.art/graph-assets/deploy/apr20/apr20_deploy_bootstrap.ps1).Content
   ```
   Installs Arena watchdog + downloads Windows-update blocker + synthetic kill-Arena test.
4. Prav: install the new dongle.
5. Prav: Tailscale — sign in on 3090, invite `zaldarren@gmail.com`. Darren tests `ssh windows-desktop-tailscale`.
6. Prav: physical check — is there a mic on the 3090? where does audio-out go? camera? (answers feed silence detector).
7. Darren runs Windows-update block, with Prav watching.
   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\Users\user\windows_update_block.ps1
   ```
8. Smoke-test: visitor prompt from phone → wall. Audio audible.

Prav catches 11:50 ferry. Darren continues remotely after.

Full operator version: `docs/apr20-morning-checklist.md`
