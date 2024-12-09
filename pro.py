import json

# Constants for emission factors (example values; refine these for real use)
EMISSION_FACTORS = {
    "electricity_kwh": 0.233,  # kg CO2 per kWh
    "miles_driven": 0.404,    # kg CO2 per mile
    "flight_hours": 90.0,     # kg CO2 per hour of flight
    "meat_meals": 5.0,        # kg CO2 per meal
}

# Function to calculate carbon footprint
def calculate_footprint(data):
    footprint = 0
    footprint += data.get("electricity_kwh", 0) * EMISSION_FACTORS["electricity_kwh"]
    footprint += data.get("miles_driven", 0) * EMISSION_FACTORS["miles_driven"]
    footprint += data.get("flight_hours", 0) * EMISSION_FACTORS["flight_hours"]
    footprint += data.get("meat_meals", 0) * EMISSION_FACTORS["meat_meals"]
    return footprint

# Function to provide suggestions
def provide_suggestions(data):
    suggestions = []
    if data.get("electricity_kwh", 0) > 500:
        suggestions.append("Consider using renewable energy sources or reducing electricity usage.")
    if data.get("miles_driven", 0) > 1000:
        suggestions.append("Consider carpooling or using public transport.")
    if data.get("flight_hours", 0) > 10:
        suggestions.append("Reduce air travel or opt for carbon offset programs.")
    if data.get("meat_meals", 0) > 20:
        suggestions.append("Reduce meat consumption or try plant-based meals.")
    return suggestions

# Main Program
def main():
    print("Welcome to the Carbon Footprint Monitoring Tool!")
    data = {}
    data["electricity_kwh"] = float(input("Enter electricity usage (kWh): "))
    data["miles_driven"] = float(input("Enter miles driven by car: "))
    data["flight_hours"] = float(input("Enter hours of flight travel: "))
    data["meat_meals"] = int(input("Enter number of meat-based meals consumed: "))

    # Calculate the footprint
    footprint = calculate_footprint(data)
    print(f"\nYour total carbon footprint is: {footprint:.2f} kg CO2")

    # Provide suggestions
    suggestions = provide_suggestions(data)
    print("\nSuggestions to reduce your carbon footprint:")
    for suggestion in suggestions:
        print(f"- {suggestion}")

    # Save report
    with open("carbon_footprint_report.json", "w") as file:
        json.dump({"data": data, "footprint": footprint, "suggestions": suggestions}, file)
    print("\nReport saved as 'carbon_footprint_report.json'.")

# Run the program
if __name__ == "__main__":
    main()
