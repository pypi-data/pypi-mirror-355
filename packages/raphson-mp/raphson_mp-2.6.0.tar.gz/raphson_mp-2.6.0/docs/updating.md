# Updating

Please check the release notes to see if there are any breaking changes.

## Pipx

```
pipx install --upgrade 'raphson-mp[online]'
```
or
```
pipx install --upgrade 'raphson-mp[offline]'
```

## Docker

1. Enter the correct directory
2. Run `docker compose pull` to download new images
4. Run `docker compose up -d` to recreate the containers

## Legacy migrations

If your previous update was before 2023-10-28, use the [migrations wiki page](./migrations.md) to update your database.
