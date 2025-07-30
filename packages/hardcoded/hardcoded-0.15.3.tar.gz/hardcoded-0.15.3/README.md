![PyPI - Downloads](https://img.shields.io/pypi/dm/hardcoded)

This package wants to replace your `hardcoded.password`, your `hardcoded.api_key`, actually  `hardcoded("Everything you really shouldn't be hardcoding")`.

## Try it!
To move a hardcoded value from your code to an external file, use `hardcoded.foo` as if it was holding your value already.
```python
import hardcoded
print(hardcoded.foo)
```

## How does it work?
On running the code, this will happen:
- if an environment variable exist with exactly the same name ("foo" in our example), the value of that environment variable is returned
- if a .env file exists in the current or any parent directory with the variable ("foo" in our example), the value of that .env variable is returned
- otherwise, hardcoded will find a file holding your data
    - if you initialised hardcoded as `hardcoded.File(path='secrets.yml')`, secrets.yml is used
    - if you are running code inside a git repository, .hardcoded.yml is used, at the root of the repository (next to .git/)
    - otherwise, ~/.config/hardcoded.yml is used
    - if the file is encrypted:
        - with GPG, then hardcoded interfaces with your GPG installation (possibly using the gpg-agent)
        - if symmetric encryption was used:
            - if a password was cached, it is used to decrypt the data
            - if Apple Keychain is available, a password is requested to decrypt the data
            - if running interactively, you will be asked for a decryption password
    - the (decrypted if needed) YAML data is loaded
    - if "foo" is a key in the YAML, the value of that key is returned
    - if "foo" does not exist in the YAML yet:
        - if not running interactively (stdin is not an open TTY), a KeyError is raised
        - if running interactively, you are asked to input the value
            - if encryption is requested with `hardcoded.File(secret=True)`, the YAML is encrypted:
                - if GPG is available, the YAML is GPG encrypted with a key of your choosing
                - if Apple Keychain is available, a random password is generated and stored in the keychain
                - otherwise, you are asked for a new password
- the value of foo is returned to your code
