# vehicle-resale-inventory-api
Repository to keep the code of an Inventory Service API. This service is dedined to be integrated with Amazon EventBridge, API Gateway, and Cognito.

# Endpoints:

    GET /api/vehicles/vehicles/ (List all vehicles filtered by is_sold)
    POST /api/vehicles/vehicles/ (Create a new vehicle)
    GET /api/vehicles/vehicles/<id>/ (Retrieve details of a specific vehicle by its ID)
    PUT /api/vehicles/vehicles/<id>/ (Update an existing vehicle)
    POST /api/vehicles/vehicles/select-vehicle/ (Select a vehicle by vehicle_id (requires vehicle_id in the request data))
    GET /api/vehicles/vehicles/confirm-withdrawal/ (Confirm the withdrawal of a selected vehicle (requires vehicle_id in the request data, and the user must be an admin))
    POST /api/vehicles/vehicles/event-handler/ (Handle events)
