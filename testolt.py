import paramiko
import time
import re
import csv
import os
from datetime import datetime

# === OLT Connection Details ===
OLT_IP = "172.16.16.11"
USER1 = "admin"
PASS1 = "Admins"
USER2 = "admin"
PASS2 = "Admins"

BASE_DIR = r"C:\DEVPROJECTS"

# Generate timestamp for filenames
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RAW_OUTPUT_FILE = os.path.join(BASE_DIR, f"olt_raw_output_{timestamp}.txt")
CSV_OUTPUT_FILE = os.path.join(BASE_DIR, f"onu_final_data_{timestamp}.csv")


def read_available(shell, read_timeout=2.0, poll_interval=0.1):
    end_time = time.time() + read_timeout
    chunks = []
    while time.time() < end_time:
        if shell.recv_ready():
            data = shell.recv(16384).decode(errors="ignore")
            if data:
                chunks.append(data)
                end_time = time.time() + read_timeout
        else:
            time.sleep(poll_interval)
    return "".join(chunks)


def parse_stats_table(raw_text):
    rows = []
    seen_header = False
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('-'):
            continue
        if line.upper().startswith("ONU-ID") and seen_header:
            continue
        if line.upper().startswith("ONU-ID"):
            seen_header = True
            continue
        cols = re.split(r'\s{2,}|\t+', line)
        if len(cols) >= 3:
            rows.append({
                "ONU-ID": cols[0],
                "Status": cols[1],
                "MAC ADDRESS": cols[2]
            })
    return rows


def parse_opm_table(raw_text):
    rows = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith('='):
            continue
        cols = re.split(r'\s{2,}|\t+', line)
        if cols:
            rows.append(cols)
    if not rows:
        raise Exception("OPM-Diag output empty or unparsable")
    header = rows[0]
    data = {row[0]: row for row in rows[1:] if len(row) >= 1}
    return header, data


def connect_and_create_csv():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {OLT_IP} ...")
        ssh.connect(
            OLT_IP,
            username=USER1,
            password=PASS1,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        shell = ssh.invoke_shell()
        time.sleep(1.0)

        output = read_available(shell)
        print(output)

        # Double login
        if re.search(r"[Ll]ogin", output):
            print("OLT asking for second username...")
            shell.send(USER2 + "\n")
            time.sleep(1.0)
            output += read_available(shell)
            print(output)
        if re.search(r"[Pp]assword", output):
            print("OLT asking for second password...")
            shell.send(PASS2 + "\n")
            time.sleep(1.5)
            output += read_available(shell)
            print(output)

        # Enable
        print("Sending 'enable' ...")
        shell.send("enable\n")
        time.sleep(1.5)
        enable_output = read_available(shell)
        output += enable_output
        print(enable_output)
        if re.search(r"[Pp]assword", enable_output):
            print("OLT asking for password after 'enable' ...")
            shell.send(PASS2 + "\n")
            time.sleep(1.5)
            output += read_available(shell)
            print(output)

        # Terminal length 0
        print("Sending 'terminal length 0' ...")
        shell.send("terminal length 0\n")
        time.sleep(1.0)
        tl_output = read_available(shell)
        output += tl_output
        print(tl_output)

        # Configure terminal
        print("Sending 'configure terminal' ...")
        shell.send("configure terminal\n")
        time.sleep(2.0)
        cfg_output = read_available(shell)
        output += cfg_output
        print(cfg_output)

        # Show onu statistics all
        print("Sending 'show onu statistics all' ...")
        shell.send("show onu statistics all\n")
        time.sleep(5.0)
        stats_output = read_available(shell, read_timeout=5.0)
        output += stats_output
        print(stats_output)

        # Show onu opm-diag all
        print("Sending 'show onu opm-diag all' ...")
        shell.send("show onu opm-diag all\n")
        time.sleep(5.0)
        opm_output = read_available(shell, read_timeout=5.0)
        output += opm_output
        print(opm_output)

        # Save raw output
        with open(RAW_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n✅ Raw output saved to: {RAW_OUTPUT_FILE}")

        # Parse statistics
        stats_data = parse_stats_table(stats_output)

        # Parse OPM-Diag
        opm_header, opm_data = parse_opm_table(opm_output)

        # Build final CSV
        final_rows = []
        final_header = ["ONU-ID", "Status", "MAC ADDRESS"] + opm_header[1:]
        final_rows.append(final_header)

        for stat in stats_data:
            onu_id = stat["ONU-ID"]
            status = stat["Status"]
            mac = stat["MAC ADDRESS"]
            opm_row = opm_data.get(onu_id)
            if opm_row:
                row = [onu_id, status, mac] + opm_row[1:]
            else:
                row = [onu_id, status, mac] + [""] * (len(opm_header) - 1)
            final_rows.append(row)

        # Write CSV
        with open(CSV_OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(final_rows)
        print(f"\n✅ Final CSV written to: {CSV_OUTPUT_FILE}")

    except Exception as e:
        print("❌ Error:", e)
    finally:
        ssh.close()


if __name__ == "__main__":
    connect_and_create_csv()
