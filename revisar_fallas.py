import sqlite3

def revisar_y_entrenar():
    conn = sqlite3.connect('motoia_aprendizaje.db')
    cursor = conn.cursor()
    
    # Buscamos diagnósticos que aún no han sido validados por el mecánico
    cursor.execute('SELECT id, descripcion_usuario, respuesta_ia FROM diagnosticos WHERE es_correcta = 0')
    fallas = cursor.fetchall()
    
    if not fallas:
        print("\n✅ ¡No hay fallas pendientes por revisar! La IA está al día.")
        return

    print(f"\n--- Panel de Entrenamiento MotoFix (Pendientes: {len(fallas)}) ---")
    
    for id_falla, desc, resp in fallas:
        print(f"\nID: {id_falla}")
        print(f"Usuario dijo: {desc}")
        print(f"IA respondió: {resp}")
        
        opcion = input("\n¿La respuesta fue correcta? (s/n) o (q) para salir: ").lower()
        
        if opcion == 's':
            cursor.execute('UPDATE diagnosticos SET es_correcta = 1 WHERE id = ?', (id_falla,))
            print("✔ Marcada como correcta.")
        elif opcion == 'n':
            correccion = input("Escribe la corrección real del mecánico: ")
            cursor.execute('''
                UPDATE diagnosticos 
                SET correccion_mecanico = ?, es_correcta = 1 
                WHERE id = ?
            ''', (correccion, id_falla))
            print("📝 Corrección guardada. La IA usará esto para aprender.")
        elif opcion == 'q':
            break
            
    conn.commit()
    conn.close()
    print("\nSesión de entrenamiento finalizada.")

if __name__ == "__main__":
    revisar_y_entrenar()