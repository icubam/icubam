Web API
=======

This page summarizes the API endpoints that are exposed by different ICUBAM services.
Note that you may need a prefix to the listed URLs depending on the deployment options
(and in particular the ``base_url`` config parameter of each service).

Main service
------------

.. http:get:: /

   Shows the map with ICUS. Requires the user to be authenticated.

.. http:get:: /map

   Shows the map with ICUS. Same as / endpoint but accessed with an API KEY.

   :query API_KEY: a valid API KEY of type ``MAP`` or ``ALL``.

.. http:get:: /version

   Returns the current version.

   **Example response**

   .. sourcecode:: json

       {'data': {
          'version': 'v0.5.1',
          'git-hash': '7416eefc',
          'bed_counts.last_modified': '2020-05-29 12:00'
          }
        }

.. http:get:: /consent

   A HTTP page with consent handler.

.. http:get:: /disclamer
 
   Shows a disclaimer page specified in the configuration.

.. http:get:: /error

   Renders the error template.

.. http:get:: /update

   Get a form to update bed counts information for an ICU

   :query id: authentication token which encodes user id and ICU id.


.. http:get:: /dashboard

   :query API_KEY: a valid API KEY of type ``STATS`` or ``ALL``.

Analytics service
-----------------

.. http:get:: /db/(str:resource)

   Export a given resource. Supported resources are ``bedcounts``, ``all_bedcounts``,
   ``icus``, ``regions``.

   :query format: The format of the response. Possible values are ``csv`` or ``html``.
   :query max_ts: Maximum timestamp for the response.

   :query API_KEY: a valid API KEY of type ``STATS`` or ``ALL``.

.. http:post:: /db/(str:resource)

   Import a given resource. The only supported resource is `bedcounts` at present.

   :query API_KEY: a valid API KEY of type ``STATS`` or ``ALL``.
   :query format: File format. Must be set to ``ror_idf``.


Backoffice service
------------------

The backoffice server does not expose a public API and is intended to be used a
web application directly.

Messaging service
-----------------

.. http:post:: /onoff

   Enable or disable messaging for a set of users. The information is encoded
   in the request body as a JSON containing ``user_id``, ``icu_ids`` and ``od``
   fields.

.. http:get:: /schedule

   This handler returns all the scheduled messages information.
