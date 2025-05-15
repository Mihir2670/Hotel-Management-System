import datetime
import json
import os
from typing import Dict, List, Optional

class Room:
    def __init__(self, room_number: str, room_type: str, price_per_night: float, is_occupied: bool = False):
        self.room_number = room_number
        self.room_type = room_type
        self.price_per_night = price_per_night
        self.is_occupied = is_occupied

    def __str__(self):
        return (f"Room {self.room_number} - Type: {self.room_type}, "
                f"Price: ${self.price_per_night}/night, "
                f"Status: {'Occupied' if self.is_occupied else 'Available'}")

class Guest:
    def __init__(self, guest_id: str, name: str, email: str, phone: str):
        self.guest_id = guest_id
        self.name = name
        self.email = email
        self.phone = phone

    def __str__(self):
        return f"Guest {self.guest_id}: {self.name}, Email: {self.email}, Phone: {self.phone}"

class Reservation:
    def __init__(self, reservation_id: str, guest: Guest, room: Room, 
                 check_in_date: datetime.date, check_out_date: datetime.date):
        self.reservation_id = reservation_id
        self.guest = guest
        self.room = room
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.is_checked_in = False
        self.is_checked_out = False
        self.services_used = []  # List of service names and prices
        self.total_charges = room.price_per_night * ((check_out_date - check_in_date).days)

    def add_service(self, service_name: str, price: float):
        self.services_used.append((service_name, price))
        self.total_charges += price

    def calculate_total_charges(self):
        nights = (self.check_out_date - self.check_in_date).days
        room_charges = self.room.price_per_night * nights
        service_charges = sum(price for _, price in self.services_used)
        return room_charges + service_charges

    def __str__(self):
        return (f"Reservation {self.reservation_id}: {self.guest.name} in Room {self.room.room_number}\n"
                f"Check-in: {self.check_in_date}, Check-out: {self.check_out_date}\n"
                f"Status: {'Checked in' if self.is_checked_in else 'Not checked in'}, "
                f"{'Checked out' if self.is_checked_out else 'Not checked out'}\n"
                f"Total Charges: ${self.total_charges:.2f}")

class Hotel:
    def __init__(self, name: str):
        self.name = name
        self.rooms: Dict[str, Room] = {}
        self.guests: Dict[str, Guest] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.next_reservation_id = 1

    def add_room(self, room: Room):
        if room.room_number in self.rooms:
            raise ValueError(f"Room {room.room_number} already exists")
        self.rooms[room.room_number] = room

    def add_guest(self, guest: Guest):
        if guest.guest_id in self.guests:
            raise ValueError(f"Guest {guest.guest_id} already exists")
        self.guests[guest.guest_id] = guest

    def make_reservation(self, guest_id: str, room_number: str, 
                         check_in_date: datetime.date, check_out_date: datetime.date) -> Reservation:
        if guest_id not in self.guests:
            raise ValueError(f"Guest {guest_id} not found")
        if room_number not in self.rooms:
            raise ValueError(f"Room {room_number} not found")
        
        room = self.rooms[room_number]
        if room.is_occupied:
            raise ValueError(f"Room {room_number} is already occupied")
        
        # Check if room is available for the requested dates
        for reservation in self.reservations.values():
            if reservation.room.room_number == room_number:
                if (check_in_date < reservation.check_out_date and 
                    check_out_date > reservation.check_in_date):
                    raise ValueError(f"Room {room_number} is not available for the selected dates")
        
        reservation_id = f"RES-{self.next_reservation_id}"
        self.next_reservation_id += 1
        
        guest = self.guests[guest_id]
        reservation = Reservation(reservation_id, guest, room, check_in_date, check_out_date)
        self.reservations[reservation_id] = reservation
        return reservation

    def check_in(self, reservation_id: str):
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} not found")
        
        reservation = self.reservations[reservation_id]
        if reservation.is_checked_in:
            raise ValueError(f"Reservation {reservation_id} is already checked in")
        
        reservation.is_checked_in = True
        reservation.room.is_occupied = True

    def check_out(self, reservation_id: str):
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} not found")
        
        reservation = self.reservations[reservation_id]
        if not reservation.is_checked_in:
            raise ValueError(f"Reservation {reservation_id} is not checked in")
        if reservation.is_checked_out:
            raise ValueError(f"Reservation {reservation_id} is already checked out")
        
        reservation.is_checked_out = True
        reservation.room.is_occupied = False
        reservation.total_charges = reservation.calculate_total_charges()

    def get_available_rooms(self, check_in: datetime.date, check_out: datetime.date) -> List[Room]:
        available_rooms = []
        
        for room in self.rooms.values():
            is_available = True
            
            # Check if room is occupied
            if room.is_occupied:
                is_available = False
            else:
                # Check reservations for this room
                for reservation in self.reservations.values():
                    if reservation.room.room_number == room.room_number:
                        if (check_in < reservation.check_out_date and 
                            check_out > reservation.check_in_date):
                            is_available = False
                            break
            
            if is_available:
                available_rooms.append(room)
        
        return available_rooms

    def save_to_file(self, filename: str):
        data = {
            "name": self.name,
            "next_reservation_id": self.next_reservation_id,
            "rooms": [
                {
                    "room_number": room.room_number,
                    "room_type": room.room_type,
                    "price_per_night": room.price_per_night,
                    "is_occupied": room.is_occupied
                }
                for room in self.rooms.values()
            ],
            "guests": [
                {
                    "guest_id": guest.guest_id,
                    "name": guest.name,
                    "email": guest.email,
                    "phone": guest.phone
                }
                for guest in self.guests.values()
            ],
            "reservations": [
                {
                    "reservation_id": res.reservation_id,
                    "guest_id": res.guest.guest_id,
                    "room_number": res.room.room_number,
                    "check_in_date": res.check_in_date.isoformat(),
                    "check_out_date": res.check_out_date.isoformat(),
                    "is_checked_in": res.is_checked_in,
                    "is_checked_out": res.is_checked_out,
                    "services_used": res.services_used,
                    "total_charges": res.total_charges
                }
                for res in self.reservations.values()
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load_from_file(cls, filename: str) -> 'Hotel':
        with open(filename, 'r') as f:
            data = json.load(f)
        
        hotel = cls(data["name"])
        hotel.next_reservation_id = data["next_reservation_id"]
        
        # Load rooms
        for room_data in data["rooms"]:
            room = Room(
                room_data["room_number"],
                room_data["room_type"],
                room_data["price_per_night"],
                room_data["is_occupied"]
            )
            hotel.rooms[room.room_number] = room
        
        # Load guests
        for guest_data in data["guests"]:
            guest = Guest(
                guest_data["guest_id"],
                guest_data["name"],
                guest_data["email"],
                guest_data["phone"]
            )
            hotel.guests[guest.guest_id] = guest
        
        # Load reservations
        for res_data in data["reservations"]:
            guest = hotel.guests[res_data["guest_id"]]
            room = hotel.rooms[res_data["room_number"]]
            
            reservation = Reservation(
                res_data["reservation_id"],
                guest,
                room,
                datetime.date.fromisoformat(res_data["check_in_date"]),
                datetime.date.fromisoformat(res_data["check_out_date"])
            )
            
            reservation.is_checked_in = res_data["is_checked_in"]
            reservation.is_checked_out = res_data["is_checked_out"]
            reservation.services_used = res_data["services_used"]
            reservation.total_charges = res_data["total_charges"]
            
            hotel.reservations[reservation.reservation_id] = reservation
        
        return hotel

def display_menu():
    print("\nHotel Management System")
    print("1. Add Room")
    print("2. Add Guest")
    print("3. Make Reservation")
    print("4. Check In")
    print("5. Check Out")
    print("6. View Available Rooms")
    print("7. View All Reservations")
    print("8. Add Service to Reservation")
    print("9. Save Data")
    print("10. Load Data")
    print("11. Exit")

def main():
    hotel = Hotel("Grand Hotel")
    
    # Sample data for demonstration
    if not os.path.exists("hotel_data.json"):
        # Add some sample rooms
        hotel.add_room(Room("101", "Single", 99.99))
        hotel.add_room(Room("102", "Double", 149.99))
        hotel.add_room(Room("201", "Suite", 249.99))
        hotel.add_room(Room("202", "Double", 149.99))
        
        # Add some sample guests
        hotel.add_guest(Guest("G001", "John Doe", "john@example.com", "555-0101"))
        hotel.add_guest(Guest("G002", "Jane Smith", "jane@example.com", "555-0102"))
    
    while True:
        display_menu()
        choice = input("Enter your choice: ")
        
        try:
            if choice == "1":
                # Add Room
                room_number = input("Enter room number: ")
                room_type = input("Enter room type: ")
                price = float(input("Enter price per night: "))
                hotel.add_room(Room(room_number, room_type, price))
                print(f"Room {room_number} added successfully.")
            
            elif choice == "2":
                # Add Guest
                guest_id = input("Enter guest ID: ")
                name = input("Enter guest name: ")
                email = input("Enter guest email: ")
                phone = input("Enter guest phone: ")
                hotel.add_guest(Guest(guest_id, name, email, phone))
                print(f"Guest {guest_id} added successfully.")
            
            elif choice == "3":
                # Make Reservation
                guest_id = input("Enter guest ID: ")
                room_number = input("Enter room number: ")
                check_in = input("Enter check-in date (YYYY-MM-DD): ")
                check_out = input("Enter check-out date (YYYY-MM-DD): ")
                
                check_in_date = datetime.date.fromisoformat(check_in)
                check_out_date = datetime.date.fromisoformat(check_out)
                
                reservation = hotel.make_reservation(guest_id, room_number, check_in_date, check_out_date)
                print(f"Reservation created successfully:\n{reservation}")
            
            elif choice == "4":
                # Check In
                reservation_id = input("Enter reservation ID: ")
                hotel.check_in(reservation_id)
                print(f"Reservation {reservation_id} checked in successfully.")
            
            elif choice == "5":
                # Check Out
                reservation_id = input("Enter reservation ID: ")
                hotel.check_out(reservation_id)
                reservation = hotel.reservations[reservation_id]
                print(f"Reservation {reservation_id} checked out successfully.")
                print(f"Total charges: ${reservation.total_charges:.2f}")
            
            elif choice == "6":
                # View Available Rooms
                check_in = input("Enter check-in date (YYYY-MM-DD, leave empty for today): ")
                check_out = input("Enter check-out date (YYYY-MM-DD, leave empty for tomorrow): ")
                
                check_in_date = datetime.date.fromisoformat(check_in) if check_in else datetime.date.today()
                check_out_date = datetime.date.fromisoformat(check_out) if check_out else datetime.date.today() + datetime.timedelta(days=1)
                
                available_rooms = hotel.get_available_rooms(check_in_date, check_out_date)
                print(f"\nAvailable Rooms from {check_in_date} to {check_out_date}:")
                for room in available_rooms:
                    print(room)
            
            elif choice == "7":
                # View All Reservations
                print("\nAll Reservations:")
                for reservation in hotel.reservations.values():
                    print(reservation)
                    print("-" * 50)
            
            elif choice == "8":
                # Add Service to Reservation
                reservation_id = input("Enter reservation ID: ")
                service_name = input("Enter service name: ")
                service_price = float(input("Enter service price: "))
                
                if reservation_id not in hotel.reservations:
                    print("Reservation not found")
                else:
                    hotel.reservations[reservation_id].add_service(service_name, service_price)
                    print(f"Service '{service_name}' added to reservation {reservation_id}")
            
            elif choice == "9":
                # Save Data
                filename = input("Enter filename to save (default: hotel_data.json): ") or "hotel_data.json"
                hotel.save_to_file(filename)
                print(f"Data saved to {filename}")
            
            elif choice == "10":
                # Load Data
                filename = input("Enter filename to load (default: hotel_data.json): ") or "hotel_data.json"
                if os.path.exists(filename):
                    hotel = Hotel.load_from_file(filename)
                    print(f"Data loaded from {filename}")
                else:
                    print(f"File {filename} not found")
            
            elif choice == "11":
                # Exit
                print("Exiting Hotel Management System. Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
