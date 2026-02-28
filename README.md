# StreetViewLocate

**StreetViewLocate** is an AutoCAD plugin that connects your CAD drawings with **Google Street View** in real time.

Select any point in your drawing and instantly open Street View at that exact geographic location - with live synchronization between AutoCAD and Street View.

This tool is designed for civil engineers, BIM engineers, highway designers, surveyors, and planners who want real-world visual context directly inside AutoCAD.

---

## ✨ Features

* 📍 **One-Click Street View Access**
  Select a point in AutoCAD and open the exact location in Google Street View.

* 🔄 **Live Direction Sync**
  A dynamic block updates in AutoCAD as you rotate or move inside Street View.

* 🧭 **Supports Coordinate Systems (UTM / EPSG Mapping)**
  Automatically maps AutoCAD coordinate systems to EPSG codes.

* 🧩 **Seamless AutoCAD Integration**
  Runs as a native .NET AutoCAD plugin.

---

## 🚀 Installation

### ✅ Recommended Method (Automatic Setup - Easiest)

1. Go to the **Latest Release** section of this repository.

2. Download the attached **Setup (.exe)** file.

3. Run the setup file.

4. The installer will automatically configure the plugin for:

   * AutoCAD 2023
   * AutoCAD 2024
   * AutoCAD 2025

   (No manual configuration required.)

5. Open AutoCAD.

6. Type the command:

```
STREETVIEWLOCATE
```

And you're ready to use it 🎉

---

### 🛠️ Manual Installation (For Developers)

1. Clone this repository:

   ```bash
   git clone https://github.com/BHUTUU/streetViewLocate.git
   ```

2. Open the `.sln` file in Visual Studio.

3. Build the project to generate:

```
StreetViewLocate.dll
```
4. Move the StreetViewBySumanKumarBHUTUU folder into C:\\Users\{yourUserName}\AppData\local\
   
5. In AutoCAD, run:

```
APPLOAD
```

7. Load the generated DLL file.

---

## 💡 How to Use

1. Open any drawing in AutoCAD.
2. Run the command:

   ```
   STREETVIEWLOCATE
   ```
3. Select a point in the drawing.
4. Street View will open at the corresponding real-world location.
5. Navigate inside Street View - and watch the AutoCAD block update live with direction and position.

---

## 🏗️ Use Cases

* Highway alignment verification
* Site condition validation
* Utility planning
* Urban development planning
* Pre-construction visualization

---

## 📁 Project Structure

```
streetViewLocate/
│
├── Properties/
├── StreetViewBySumanKumarBHUTUU/
├── setup/
├── .gitignore
├── LICENSE
├── README.md
├── StreetViewLocate.cs
├── StreetViewLocate.csproj
├── StreetViewLocate.slnx
└── app.config
```

---

## 🤝 Contributing

Pull requests and feature suggestions are welcome.

If you’d like to improve performance, coordinate system handling, UI, or WebView integration - feel free to contribute.

---

## 📜 License

This project is licensed under the MIT License.

---
