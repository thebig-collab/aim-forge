# יצירת AimForge ל-Windows בלי להתקין Python במחשב שלך

הדרך הקלה היא לבנות את התוכנה ב-GitHub Actions (מחשב Windows בענן):
1. צור חשבון GitHub אם אין לך.
2. צור Repository חדש והעלה אליו את כל התיקייה והתוכן של הפרויקט, כולל תיקיית `.github`.
3. היכנס ללשונית **Actions** ואשר הפעלת Workflows אם GitHub מבקש.
4. בחר **Build AimForge for Windows** ולחץ **Run workflow**.
5. כשהריצה מסתיימת בהצלחה, פתח אותה והורד את הקובץ **AimForge-Windows** תחת Artifacts.
6. חלץ את ZIP והפעל `AimForge.exe` שבתוכו. אין צורך להתקין Python במחשב שבו מריצים את AimForge.

הערות:
- ה-Workflow משתמש ב-Python רק במחשב Windows זמני של GitHub כדי לבנות את התוכנה; הוא לא מותקן במחשב שלך.
- זו גרסת Starter, לא המוצר המלא שתואר. יש לבדוק את קובץ ה-EXE ב-Windows לפני הפצה.
- אם רוצים קובץ התקנה יחיד `AimForge_Setup.exe`, צריך להריץ את Inno Setup על `dist/AimForge.exe` לאחר הבנייה; `installer.iss` כלול בפרויקט.
