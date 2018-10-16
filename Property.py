class Property:

    def __init__(self, id, user_id, title = "", property_description = "", image = [], location = "", guests = 0):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.property_description = property_description
        self.image = image
        self.location = location
        self.guests = guests
