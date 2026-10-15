# Page file change: what was done and how to undo it

Date: 2026-10-15. PC: the one in [`../audit-rtx5090-285k.json`](../audit-rtx5090-285k.json).

## Before (saved in `state-before.json`, `state-before-apply.json`)

| | |
|---|---|
| page file | `C:\pagefile.sys`, **system-managed** (`AutomaticManagedPagefile = True`, no `Win32_PageFileSetting`), allocated 21.5-26.7 GB (it moves) |
| registry `PagingFiles` | `?:\pagefile.sys` (automatic) |
| commit limit | 84.4-89.5 GB (varies with the managed size); 87.8 GB committed with Strata running (1.7 GB left) |
| crash dumps | `CrashDumpEnabled = 3` (small memory dump), `DumpFile = C:\windows\MEMORY.DMP`, `AutoReboot = 1`, `Overwrite = 1` - **not touched** |
| disk | `C:` 1906 GB, 975 GB free; `E:` 7452 GB, 5058 GB free |

## Change

`scripts/pagefile_set.ps1 -SizeMB 49152` (elevated): automatic management off, `C:\pagefile.sys` initial = maximum =
**49152 MB (48 GiB)**, applied through the supported `Win32_PageFileSetting` WMI class. It refuses unless the drive keeps
200 GB free. Transcript: [`pagefile-apply.log`](pagefile-apply.log) (user and host name removed).

Windows applies it at the **next boot**; until then `Win32_PageFileUsage` and the commit limit are unchanged (checked:
commit limit stayed at 90.5 GB, registry already shows `C:\pagefile.sys 49152 49152`). **Nothing was restarted by the
tool.**

48 GiB of commit raises the limit from ~85-89 GB to ~111 GB. Physical RAM is unchanged (63.4 GB): the page file only
raises how much *commit* Windows will grant, which is what bounds pinned memory and VRAM allocations.

## Undo

Elevated PowerShell, then restart:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pagefile_rollback.ps1
```

(removes the custom setting and turns automatic management back on.) Or by hand: System > About > Advanced system
settings > Performance > Settings > Advanced > Virtual memory > tick "Automatically manage paging file size for all
drives" > OK > restart. The 48 GiB file is deleted by Windows at the next boot after that.

## After

`state-after-reboot.json` (same script, `scripts/pagefile_state.ps1`) is added once the PC has restarted.
