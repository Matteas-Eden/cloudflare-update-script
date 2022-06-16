# CloudFlare DNS Record Update Script
A small Python script to update a single A record on CloudFlare's servers.
Configuration variables are loaded in from a local `.env` file, and a template
service file for use with systemd is included.

## Configuration
In order to configure the script, you may copy the `.env.template` file into
`.env` and populate the fields within. Here's a breakdown of the variables:

| Name              | Description                                                    |
| ----              | -----------                                                    |
| API_TOKEN*        | The API token created in CloudFlare.                           |
| RECORD_NAME*      | The name of the A record to be updated on CloudFlare.          |
| ZONE_NAME*        | The zone (domain) whose DNS table is being updated.            |
| LOGGING_FILE      | The name of the file to log to.                                |

Variables marked with a `*` are **required**.

## Usage
Using the script is simple. You may run the script manually, or you can
configure the script to run on boot via systemd. For either usage, passing the
`-s` or `--silent` parameters suppresses logging. Passing the `-d` or `--dry`
parameters also prevents the script from writing back changes to the DNS.

### Setup
A `requirements.txt` is supplied to assist with installing all of the required
dependencies. Simply run:
```
pip install -r requirements.txt
```
Once that is done, create a copy of the `.env.template` file;
```
cp .env.template .env
```
and then fill it out with your details as appropriate, adhering to the configurations outlined previously.

### Manual
To run the script manually, simply execute via the command line:
```
chmod +x cloudflareUpdateScript.py
./cloudflareUpdateScript.py
```

### On Boot
If you wish to execute the script on boot alongside other systemd services,
then you can use the `cloudflare-update-script.service.template` included in the
repository. It looks like this:
```
[Unit]
Description=Updates CloudFlare DNS Record with Public IP
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /path/to/script.py
WorkingDirectory=/path/to/
User=<user>

[Install]
WantedBy=multi-user.target
```
Similarly to setting up the environment variables, you'll want to copy this as such:
```
cp cloudflare-update-script.service.template cloudflare-update-script.service
```
Then, fill out `/path/to/script.py` with the *absolute* path
on your machine to where the `cloudflareUpdateScript.py` script is located. You
also need to replace `<user>` with the name of the user account who will be
executing the service. You'll then need to either copy the service file or symlink it into an appropriate directory (e.g. `/lib/systemd/system/`). Finally, enable it like you would any other systemd
service:

`systemctl enable cloudflare-update-script`

## License
This software is provided under the MIT license.
