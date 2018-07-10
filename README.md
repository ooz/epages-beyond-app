# ePages Beyond Example App: *Beautiful Order Documents*

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/ooz/epages-beyond-app/tree/master)

This app shows a list of orders for a configured shop.
Each order has a link, that triggers rendering a order document containing the line items as a PDF.

![Screenshot of the app](screenshot.png)

The order list for two different shops is shown.
On the left side you see the order list of the respective shop, on the right side a single generated order document.

## Running it on Heroku

1. You need to have a [developer shop for ePages Beyond](https://signup.beyondshop.cloud/epages).
2. Create a "Custom app" having at least the scope "Read orders" (`ordr:r`). Note the `client_id` and `client_secret`.
   In order to see something in the app, it is recommended that you have at least one order in your shop.
3. Click the Heroku button above. Login with your Heroku account and fill out the required environment variables:
    * `CLIENT_ID` and `CLIENT_SECRET` are the ones you just noted.
    * The `API_URL` is required for Custom apps (apps that are only active in your shop and cannot be installed in other shops).
      The `API_URL` is your shop's domain appended by `/api`, e.g.
      ```http
      https://api-shop.beyondshop.cloud/api
      ```
4. Hit the "Create app" button to deploy!

## Local Development Using Docker

```bash
# 1. Build the docker image
make docker_build

# 2. Initialize the environment variable file
make docker_init_env

# 3. Edit the env.list file, set CLIENT_ID, CLIENT_SECRET and API_URL
#    You can obtain those following steps 1. to 3. from "Running it on Heroku"

# 4. Run the app
make docker_run
```
