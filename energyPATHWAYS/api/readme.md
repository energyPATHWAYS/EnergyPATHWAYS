# energyPATHWAYS RESTful API

This readme documents the RESTful API developed for energyPATHWAYS. All API related files are found in this directory, and this readme describes each of them in turn.


# api.py

Contains the public-facing API code.

## Dependencies

The API has dependencies that are additional to the core energyPATHWAYS model. As of this writing, they are: flask, flask_bcrypt, flask_httpauth, flask_restful, flask_sqlalchemy, itsdangerous, marshmallow and sqlalchemy. I have not added these to the overall dependencies for the energyPATHWAYS package because it seems to me that it will be a common use case for users to want to download and run the model but not have any use for the API. In fact, it probably makes sense to move the API code into its own package (e.g. energyPATHWAYS_api) as it matures. In any case, for now you will need to manually install the dependencies, e.g. using `pip`, before spinning up the API.

## Running and accessing the API

Once you have the dependencies installed, a configuration file set up (see "config.py.example" below), and your database migrated (see "migrate,py" below) you can start a development web server for the API simply by entering

`python api.py`

on the command line. By default the server will listen on port 5000, so you can access, for example, the scenario list at http://localhost:5000/scenarios. While you can access the API directly from a web browser, I have found the [Postman](https://chrome.google.com/webstore/detail/postman/fhbjgbiflinjbdggehcddcbncdddomop?hl=en) Chrome app to be much more convenient, particularly when you want to control details of the HTTP request (see "HTTP/REST conventions", below).

## Security

All requests to the API are required to provide a username and password HTTP Basic Authentication. This prevents users from viewing or editing scenarios that they should not have access to. Since we will have "guest" web users who need to be able to access outputs for built-in scenarios without creating a user account, the API has a hard-coded guest profile that can be used by sending the username "guest" in the authentication header. (The password is ignored with this username.) To get Postman to send an Authorization header for you, just use the Authorization section underneath the URL field, set the drop-down to "Basic Auth", and provide the desired username and password.

API consumers can also request a secure token that will allow access to the site on behalf of the user without needing to send the actual username and password with each request, until it expires. (Currently the expiration time is set to 1 hour; see `models.User.generate_auth_token()`.) The token is available at the `/token` route. To use the returned token, simply send it as a username with a request instead of the actual username. As with guest access, the password is ignored when using token authentication.

**Warning:** this configuration will only provide true security if the API is served exclusively over HTTPS (rather than HTTP) in production. This will require some additional configuration when we deploy.

## HTTP/REST conventions

The API follows REST principles by mapping operations to HTTP methods in predictable ways; essentially, GET is for reading data, POST is for creating new resources, PUT is for updating existing resources, and DELETE (not yet implemented here) is for deleting. These methods are directly mapped to instance methods of the Resource subclasses in `api.py` (e.g. `get()`, `post()`, etc.) so it should be relatively straightforward to discover which method you are activating with a given request. See the `api.add_resource()` calls at the end of the file to see how URIs are explicitly mapped to Resources.

To exercise the entire API, you will need to change the HTTP method at the beginning of the URI in Postman. For POST and PUT requests you will also need to provide a request body in json format (use the "Body" section below the URI) and provide a `Content-Type: application/json` header (use the "Headers" section) so that the API knows how to interpret the request body. The unit tests (see test_api.py below) should give you a good idea of what contents are expected in the body; we can document this in more detail as the specifics stabilize.

The API attempts to return informative HTTP status codes when a problem is encountered. E.g. making a request without sending an HTTP authentication header will result in a "401 Unauthorized" response, attempting to edit a scenario that one does not own will result in "403 Forbidden", and attempting to retrieve a scenario that does not exist will result in "404 Not Found". Successful requests will generally have a "200 Success" status code, except when resources are created (e.g. a new scenario), which will return "201 Created".

## Unfinished business

Note that the API does not yet actually run the requested scenario when you POST to `/scenarios/<scenario_id>`, because the single point of contact to run a model is not yet available. It does do everything it can to set up a run, though.


# config.py.example

This is an example configuration file for the API. You will, at a minimum, need to copy the file to `config.py` and edit the SQLALCHEMY_DATABASE_URI in the copy to be correct for your setup. You should also replace the SECRET_KEY with something long and random to ensure the security of token authentication, and you **must** do this in any production environment; it is highly insecure to leave the example key in place!


# migrate.py

**Warning**: Be sure to back up your database before running this file! The core energyPATHWAYS code has not yet been updated to match up with this migration -- i.e., to use the new many-to-many relationships mentioned below -- so after you run the migration you should expect that API testing will work, but actual model runs will crash! You will want a clean database to return to after playing with the API.

This script takes an existing energyPATHWAYS database and performs the necessary additions and modifications to make it compatible with the API. To run it, simply enter:
 
 `python migrate.py`
 
 You will be prompted for a password for an initial administrative user (with username "admin").
 
 The most notable edit made by the migration is to change the DemandCases->DemandStates and SupplyCases->SupplyStates relationships to be many-to-many rather than one-to-many to allow the *Data rows (which the API refers to as "package groups") to be reused across different cases/scenarios. Several schemas and tables are also added to store users, status information about individual model runs, and outputs. Note that the migration will gather its database access information from your production configuration (`config.py`) so you must set that up before running `migrate.py`.


# models.py

Contains SQLAlchemy models for the various entities that the API needs access to, and also manages database access for the API and migration, via the `db` object. Note that the model classes found here are not intended for use as-is outside the API context; in particular some models such as DemandSubsector are missing fields that are essential to proper functioning of the energyPATHWAYS simulation but are not important to the API.


# schemas.py

Marshmallow schemas for the various models that need to be serialized and deserialized for the API.


# test_api.py

**Warning**: make sure you set up `test_config.py` (see below) before running the tests. The unit tests require access to a testing database, which should not be the same as your production database.

This file provides unit tests for the entire API. It can be run directly with

`python test_api.py`

or via the usual test discovery methods. So far, the focus of testing is on ensuring that the API has the correct general behavior in terms of status codes, access control, etc. Testing on the exact structure of json responses is somewhat thinner. The unit tests create and delete a pristine set of testing data for each test, so the only requirement is an empty test database to work with.


# test_config.py.example

Copy this to `test_config.py` and edit it with your unit testing configuration. Note that these settings will *override* your production configuration, so you only need to include settings here that are different from production. Probably this will just be the SQLALCHEMY_DATABASE_URI.