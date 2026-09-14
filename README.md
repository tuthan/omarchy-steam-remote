# SteamOS Remote — Omarchy plugin

SteamOS Remote is an Omarchy bar widget for controlling a paired SteamOS host
from the desktop. It is the client half of the SteamOS Remote v1 integration;
the separate Decky host owns the HTTPS API, pairing approval, and host-side
operations.

The client talks directly to the pinned host endpoint, so status and display
recovery remain available when Sunshine or the game stream is unavailable.

- Plugin ID: `io.github.tuthan.steamosremote`
- License: MIT

## Validate locally

The project has no dependency download step. From this directory:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
omarchy plugin validate .
qmllint Panel.qml
```

The Omarchy plugin is installed from its reviewed plugin directory; this
project does not generate or require a ZIP artifact.

`qmllint BarWidget.qml` on the Omarchy 4.0.3 toolchain currently exits 255
without diagnostics while parsing the host-provided `IpcHandler` typed
function syntax; the same syntax is used by installed first-party widgets.
`Panel.qml` parses successfully. The running Omarchy shell remains the final
loader check.

## Install from a reviewed repository

Omarchy plugins run as unsandboxed code inside the long-lived shell. Review the
source before enabling it, then install from the published repository or
marketplace using Omarchy’s native lifecycle:

```sh
omarchy plugin add <reviewed-git-url> --enable
```

## Local development

Omarchy expects a real plugin directory, so use `rsync` instead of a symlink:

```bash
plugin_dir="$HOME/.config/omarchy/plugins/io.github.tuthan.steamosremote"
mkdir -p "$(dirname "$plugin_dir")"
if [ -L "$plugin_dir" ]; then unlink "$plugin_dir"; fi
mkdir -p "$plugin_dir"
rsync -a --delete --exclude='.git/' "$PWD"/ "$plugin_dir"/
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.tuthan.steamosremote --section right
```

After changing `BarWidget.qml`, `Panel.qml`, or `manifest.json`, run the same
`rsync` command and rescan the shell. Do not use `omarchy plugin update` for
this local copy.

## Disable or remove

```sh
omarchy plugin disable io.github.tuthan.steamosremote
omarchy plugin remove io.github.tuthan.steamosremote
```

Removing the plugin does not remove the separately stored client credentials.

The client owns only its plugin directory. Credentials live separately under
`$XDG_STATE_HOME/steamos-remote/` (or `~/.local/state/steamos-remote/`) with
directory mode 0700 and file mode 0600. `client.json` holds the credential;
`pending.json` holds an in-flight pairing request and is removed when that
request is approved, cancelled, or expires. Removing or replacing the plugin
leaves those files intact; use **Forget local pairing** for local cleanup and
**Revoke host credential** to invalidate the server-side credential.

## User journey

1. Install and enable the widget. Open **Settings**. The three steps in that
   view are numbered in the order they have to happen.
2. Under **1 · Find the host**, choose **Find hosts**. The client scans only
   active local IPv4 subnets and sends no pairing material. Each listener is
   listed with a short form of its TLS certificate fingerprint. A single
   answer is selected automatically; when more than one listener answers,
   nothing is selected for you, because only the fingerprint shown in Decky
   identifies your Deck.
3. Under **2 · Request pairing**, choose **Request pairing**. Omarchy derives
   an 8-digit verification code from the selected host's pinned certificate
   and displays it with a 120-second countdown. The code is never sent. Decky
   derives the same code from its own certificate and shows it beside the
   pending client, so a different machine answering on that address produces
   different digits and the mismatch is visible before you approve. Compare
   the two codes, then press **Approve** in Decky. Approval automatically
   stores the endpoint, the TLS certificate pin, and the host's wake MAC.
   Omarchy selects its own active LAN interface for the packet, so there is no
   separate MAC or interface save step.
4. While a request is pending you can close the panel and come back to it, or
   press **Cancel pairing request**. The request lives in the client's private
   state, not in the panel, so waiting for approval never blocks status
   refreshes or the wake action. If discovery is not possible, open **Show
   advanced pairing and endpoint controls** and use the full payload field.
5. Use **Host** for status, Wake, Suspend, Restart, Shut down, and the
   prominently placed **Restore last known-good display** action. Each
   disruptive power action has its own confirmation; the UI reports a method
   return as requested until the host can be observed again. Uptime is shown
   as `d:h:m`, and CPU temperature is shown when the host can read a labelled
   CPU hwmon sensor. When a power capability is not `available`, the row says
   which value the host reported and a legend explains what each value means.
6. Use **Display** for an exact-target mode preview. Modes are listed largest
   first, then by highest refresh rate, with the current mode pinned to the
   top of the list. When the host advertises more than one output, the first
   row cycles between them. Every mode has its own **Preview** button only
   after that resolution is selected; the countdown, **Save**, and **Revert**
   controls stay beside the selected resolution. Save confirms the visible
   preview and stores the last known-good mode for recovery. Common refresh
   rates are shown by default; enable **Show non-standard refresh rates** in
   Settings to include entries such as 24, 30, and 75 Hz. The host's 15-second
   deadline restores the previous profile if the client disappears.

## Reading the status

The widget separates six conditions that are easy to confuse:

| Shown | Means |
|---|---|
| Not paired | No credential is stored on this machine. |
| Host unreachable | Paired, but the pinned endpoint did not answer. |
| Checking host | Paired, no observation yet in this panel session. |
| Status stale | The last successful observation is more than 15 seconds old. |
| Steam bridge unavailable | The host answered, but its Steam bridge is not ready. |
| Ready | The host answered and its Steam bridge is ready. |

Reachability is reported on its own line and never overwrites the result of
the last action you took.

The bar icon asks for attention only for something actually observed: a paired
host that refused or dropped the last request. Two other conditions dim it
instead. An unpaired widget has no problem to report. A stale reading is an
absence of knowledge rather than a failure, and it is the normal state after
the panel has been closed for a while, because nothing polls while the panel is
hidden. Hover the icon to see which of the three it is.

Closing the panel therefore does not leave a stale reading presented as if it
were current. It also means the bar will not tell you that a host went offline
while you were not looking; open the panel, or middle-click the icon, to ask.

## When the host is offline

The panel polls only while it is visible. Each cycle asks for status first and
requests the mode inventory or an operation result only after status succeeds,
so a powered-off host costs one short request per cycle instead of three. The
interval backs off to a maximum of six seconds while the host is unreachable
and returns to two seconds as soon as you take an action, so pressing **Wake
host** does not then wait out a long backoff before noticing the host return.

Sunshine is controlled by Decky's **Monitor Sunshine** setting. Omarchy does
not request a separate Sunshine pairing scope; it only shows the host status
and the restart action when Decky has monitoring enabled and the Decky Sunshine
owner is reachable through Decky Loader. If that owner is unavailable, the
client reports it instead of treating the host as stopped.

Network discovery is an explicit, bounded IPv4 scan rather than an automatic
background scan. It only lists HTTPS listeners that identify as the current
SteamOS Remote service. A matching open port is a locator, not trust: TLS
certificate pinning, the TLS channel binding, the certificate-derived
comparison code, and Decky approval still complete pairing. If channel
verification fails, select the listener again and start a new request; do not
approve a request whose code is not shown by the intended host.

Unknown, stale, disabled, and unavailable values remain distinct in the UI.
The word "Running" refers to the Sunshine process observation only; it does
not claim that capture, encoding, or a streaming session is healthy.
