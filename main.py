import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3307,  # Updated port
        user="root",
        password="12345",
        database="grocery_db"
    )

def drop_inventory_table():
    confirmation = input("Are you sure you want to drop the 'inventory' table? Type 'yes' to confirm: ")
    
    if confirmation.lower() == 'yes':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Disable foreign key checks, drop the table, and re-enable checks
            cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
            cursor.execute('DROP TABLE IF EXISTS orders;')
            cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ 'orders' table dropped successfully!")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    else:
        print("❌ Action cancelled. The 'inventory' table was not dropped.")

if __name__ == '__main__':
    drop_inventory_table()
