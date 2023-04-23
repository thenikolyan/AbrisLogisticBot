# LogisticBot

## Main idea
The main idea of the bot is to automate the transfer of documents and collect statistics about the routes traveled.

The bot is able to request a geo-location, save photos, and also notifies the administrators (logisticians) of the company.

## Registration

## Users
The structure of the user database supports 4 roles: admin, driver, clown, unauthorized, further details about each.

### Admin

The administrator manages the cargo delivery process, his duties include tracking the driver's location, as well as obtaining operational information on cargo delivery.

To simplify the work, a control panel was created for him.

The control panel contains 4 main and one universal undo button.

    - Confirmation of registration
        If there are authorization requests, the initials of the registered users will appear when you click this button. After selecting one, one of the 4 roles will be offered for assignment

        Otherwise, an alert will come that no one is waiting for registration confirmation.

    - Viewing directories 
       This subsection consists of query buttons:
        1. Viewing the list of drivers - sends the list in xlsx format
        2. View the list of routes - sends the list in xlsx format
        3. View the list of drivers and routes assigned to them - sends a list in xlsx format
        4. «Back» button - returns the user to the control panel       

    - Working with routes
        1. Create a route:
            i. The first way to create a route is manually. You need to write the number of points, and then enter the address of each point.
            ii. The second way is to make an Excel file with all the points. The bot will send an example file to fill in.
        2. Route assignment. The bot sends a list of routes to the file. Next, you need to submit an ID to the bot to choose a driver from the ones offered by the bot.
        3. Deleting a route. The bot sends a file with a list of routes. Next, you need to give him the route ID to delete.
        4. «Back» button - returns the user to the control panel

    - Collecting the report. Provides a file in Excel format about all trips.

### Driver
os.getenv('token', 'default')
«»