using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Windows;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using ProjNet.CoordinateSystems;
using ProjNet.CoordinateSystems.Transformations;
using ProjNet.SRID;
using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;

namespace StreetViewLocate
{
    public class StreetViewLocate
    {
        public static PaletteSet ps;
        public static WebView2 webView;
        public static string block_file_path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "StreetViewBySumanKumarBHUTUU", "streetViewLocate_block.dwg");
        public static readonly Dictionary<string, string> ACAD_CS_TO_EPSG = new Dictionary<string, string>
        {
            { "UTM84-40N", "32640" },
            { "UTM84-41N", "32641" },
            { "UTM84-42N", "32642" },
            { "UTM84-43N", "32643" },
            { "UTM84-44N", "32644" },
            { "UTM84-45N", "32645" },
            { "WGS84", "4326" },
            { "BRITISHNATGRID", "27700" },
            { "OSGB1936.NATIONALGRID", "27700" },
            { "WEBMERCATOR", "3857" }
        };
        string url = "https://www.google.com/maps/";
        [CommandMethod("STREETVIEWLOCATE")]
        public void StreetViewLocateCommand()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            Editor ed = doc.Editor;
            if (!File.Exists(block_file_path))
            {
                ed.WriteMessage($"\nBlock file not found at {block_file_path}. Please ensure the block file is placed at this location for the command to work.");
                return;
            }
            string coordinateSystemInFile = Autodesk.AutoCAD.ApplicationServices.Application.GetSystemVariable("CGEOCS") as string;
            if (string.IsNullOrEmpty(coordinateSystemInFile))
            {
                ed.WriteMessage("\nNo coordinate system found in this doc, please set using \"EDITDRAWINGSETTINGS\" command in Civil3D only.");
                return;
            }
            coordinateSystemInFile = coordinateSystemInFile.ToUpper();
            if (!ACAD_CS_TO_EPSG.ContainsKey(coordinateSystemInFile))
            {
                ed.WriteMessage($"\nCoordinate system '{coordinateSystemInFile}' is not supported. Please contact - Suman Kumar (bhutuu.github.io) so that he can add it.");
                return;
            }
            string coordinateSystemCodeString = ACAD_CS_TO_EPSG[coordinateSystemInFile];
            if (StreetViewLocate.ps == null)
            {
                StreetViewLocate.ps = new PaletteSet("STREETVIEWLOCATE BY SUMAN KUMAR")
                {
                    DockEnabled = DockSides.Left | DockSides.Right | DockSides.Top | DockSides.Bottom,
                    MinimumSize = new System.Drawing.Size(800, 800),
                    Style = PaletteSetStyles.ShowCloseButton | PaletteSetStyles.ShowPropertiesMenu
                };
                var control = new webPalatteControl(url);
                ps.Add("STREETVIEWLOCATE BY SUMAN KUMAR", control);
                ps.StateChanged += (sender, e) =>
                {
                    if (e.NewState == StateEventIndex.Hide)
                    {
                        StreetViewLocate.DeleteAllStreetViewBlocks();
                    }
                };
            }
            ps.Visible = true;
        }
        public static (double x, double y, bool status) GetAutoCADPoint()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            Editor ed = doc.Editor;
            PromptPointOptions ppo = new PromptPointOptions("\nSelect a point to locate in Street View:");
            PromptPointResult ppr = ed.GetPoint(ppo);
            if (ppr.Status == PromptStatus.OK)
            {
                return (ppr.Value.X, ppr.Value.Y, true);
            }
            else
            {
                return (0, 0, false);
            }
        }
        public static ObjectId PlaceBlockAtLocation(double x, double y)
        {
            string blockFilePath = block_file_path;
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            using (doc.LockDocument())
            {
                Database db = doc.Database;
                using (Transaction tr = db.TransactionManager.StartTransaction())
                {
                    BlockTable bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                    string blockName = System.IO.Path.GetFileNameWithoutExtension(blockFilePath);
                    if (!bt.Has(blockName))
                    {
                        using (Database sourceDb = new Database(false, true))
                        {
                            sourceDb.ReadDwgFile(blockFilePath, System.IO.FileShare.Read, true, "");
                            db.Insert(blockName, sourceDb, false);
                        }
                        bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                    }
                    BlockTableRecord modelSpace = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                    ObjectId blockDefId = bt[blockName];
                    BlockReference br = new BlockReference(new Autodesk.AutoCAD.Geometry.Point3d(x, y, 0), blockDefId);
                    ObjectId newId = modelSpace.AppendEntity(br);
                    tr.AddNewlyCreatedDBObject(br, true);
                    tr.Commit();
                    return newId;
                }
            }
        }
        public static void MoveBlock(ObjectId blockId, double newX, double newY, double angle)
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if(doc == null) return;
            if(blockId.IsNull || !blockId.IsValid || blockId.IsErased) return;
            if(blockId.Database != doc.Database) return;
            using (doc.LockDocument())
            using (Transaction tr = doc.Database.TransactionManager.StartTransaction())
            {
                BlockReference br = tr.GetObject(blockId, OpenMode.ForWrite) as BlockReference;
                if (br != null)
                {
                    br.Position = new Autodesk.AutoCAD.Geometry.Point3d(newX, newY, 0);
                    br.Rotation = angle;
                }
                tr.Commit();
                doc.Editor.UpdateScreen();
            }
        }
        public static void DeleteAllStreetViewBlocks()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            using (doc.LockDocument())
            using (Transaction tr = doc.Database.TransactionManager.StartTransaction())
            {
                BlockTable bt = (BlockTable)tr.GetObject(doc.Database.BlockTableId, OpenMode.ForRead);
                string blockName = Path.GetFileNameWithoutExtension(block_file_path);
                if (!bt.Has(blockName))
                {
                    tr.Commit();
                    return;
                }
                ObjectId blockDefId = bt[blockName];
                BlockTableRecord blockDef = (BlockTableRecord)tr.GetObject(blockDefId, OpenMode.ForRead);
                ObjectIdCollection refs = blockDef.GetBlockReferenceIds(true, false);
                foreach (ObjectId refId in refs)
                {
                    Entity ent = tr.GetObject(refId, OpenMode.ForWrite) as Entity;
                    ent?.Erase();
                }
                tr.Commit();
                doc.Editor.UpdateScreen();
            }
        }
    }
    public static class CoordinateConverter
    {
        public static (double lat, double lon) ToWGS84(double easting, double northing, int epsg)
        {
            CoordinateSystem sourceCS = SRIDReader.GetCSbyID(epsg);
            CoordinateSystem targetCS = SRIDReader.GetCSbyID(4326);
            var ctFactory = new CoordinateTransformationFactory();
            var transform = ctFactory.CreateFromCoordinateSystems(sourceCS, targetCS);
            double[] fromPoint = new double[] { easting, northing };
            double[] toPoint = transform.MathTransform.Transform(fromPoint);
            double lat = toPoint[1];
            double lon = toPoint[0];
            return (lat, lon);
        }
        public static (double easting, double northing) ToEastingNorthing(double lat_val, double lon_val, int epsg)
        {
            CoordinateSystem sourceCS = SRIDReader.GetCSbyID(4326);
            CoordinateSystem targetCS = SRIDReader.GetCSbyID(epsg);
            var ctFactory = new CoordinateTransformationFactory();
            var transform = ctFactory.CreateFromCoordinateSystems(sourceCS, targetCS);
            double[] fromPoint = new double[] { lon_val, lat_val };
            double[] toPoint = transform.MathTransform.Transform(fromPoint);
            double easting = toPoint[0];
            double northing = toPoint[1];
            return (easting, northing);
        }
    }
    public class webPalatteControl : UserControl
    {
        private WebView2 webView;
        private string url = string.Empty;
        private ObjectId blockId;
        private Button pickPointButton;
        public ObjectId BlockId { get => blockId;}
        public int GetCurrentDrawingEPSG()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            string coordinateSystemInFile = Autodesk.AutoCAD.ApplicationServices.Application.GetSystemVariable("CGEOCS") as string;
            if (string.IsNullOrEmpty(coordinateSystemInFile))
            {
                MessageBox.Show("\nNo coordinate system found in this doc, please set using \"EDITDRAWINGSETTINGS\" command in Civil3D only.");
                return -1;
            }
            coordinateSystemInFile = coordinateSystemInFile.ToUpper();
            if (!StreetViewLocate.ACAD_CS_TO_EPSG.ContainsKey(coordinateSystemInFile))
            {
                MessageBox.Show($"\nCoordinate system '{coordinateSystemInFile}' is not supported. Please contact - Suman Kumar (bhutuu.github.io) so that he can add it.");
                return -1;
            }
            string coordinateSystemCodeString = StreetViewLocate.ACAD_CS_TO_EPSG[coordinateSystemInFile];
            return int.Parse(coordinateSystemCodeString);
        }
        public webPalatteControl(string url_string)
        {
            url = url_string;
            this.Dock = DockStyle.Fill;
            this.BackColor = System.Drawing.SystemColors.Control;
            webView = new WebView2();
            webView.Dock = DockStyle.Fill;
            this.Controls.Add(webView);
            this.Load += WebPaletteControl_Load;
            pickPointButton = new Button();
            pickPointButton.Text = "Pick Point";
            pickPointButton.Size = new System.Drawing.Size(100, 40);
            pickPointButton.ForeColor = System.Drawing.Color.White;
            pickPointButton.BackColor = System.Drawing.Color.Blue;
            pickPointButton.Anchor = AnchorStyles.Left | AnchorStyles.Bottom;
            pickPointButton.Click += PickPointButton_Click;
            this.Resize += (s, e) =>
            {
                pickPointButton.Location = new System.Drawing.Point(1, this.Height - pickPointButton.Height - 1);
            };
            this.Controls.Add(pickPointButton);
            this.Controls.SetChildIndex(pickPointButton, 0);
        }
        private async void WebPaletteControl_Load(object sender, EventArgs e)
        {
            this.BeginInvoke(new Action(async () =>
            {
                try
                {
                    string userDataFolder = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "StreetViewLocateWebView");
                    var env = await Microsoft.Web.WebView2.Core.CoreWebView2Environment.CreateAsync(null, userDataFolder);
                    await webView.EnsureCoreWebView2Async(env);
                    webView.CoreWebView2.SourceChanged += CoreWebView2_SourceChanged;
                    webView.Source = new Uri(url);
                }
                catch (System.Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }
            }));
        }
        private void CoreWebView2_SourceChanged(object sender, CoreWebView2SourceChangedEventArgs e)
        {
            var doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if (doc != null)
            {
                string currentUrl = webView.Source?.ToString();
                var(lat, lon, heading, pitch) = parseLatLongHeadingPitchFromStreetViewUrl(currentUrl);
                if (lat != 0 && lon != 0)
                {
                    int epsgCode = GetCurrentDrawingEPSG();
                    if (epsgCode == -1) return;
                    var (easting, northing) = CoordinateConverter.ToEastingNorthing(lat, lon, epsgCode);
                    if (blockId.IsNull || !blockId.IsValid || blockId.IsErased)
                    {
                        blockId = StreetViewLocate.PlaceBlockAtLocation(easting, northing);
                    }
                    StreetViewLocate.MoveBlock(blockId, easting, northing, (360 - heading) * Math.PI / 180);
                }
            }
        }
        private (double lat, double lon, double heading, double pitch) parseLatLongHeadingPitchFromStreetViewUrl(string url)
        {
            string parse_pattern = @"@(-?\d+\.\d+),(-?\d+\.\d+),3a,[^h]*?([0-9.]+)h,([0-9.]+)t";
            var match = System.Text.RegularExpressions.Regex.Match(url, parse_pattern);
            if(match.Success)
            {
                double lat = double.Parse(match.Groups[1].Value);
                double lon = double.Parse(match.Groups[2].Value);
                double heading = double.Parse(match.Groups[3].Value);
                double pitch = double.Parse(match.Groups[4].Value);
                return (lat, lon, heading, pitch);
            }
            return (0, 0, 0, 0);
        }
        private void PickPointButton_Click(object sender, EventArgs e)
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            Editor ed = doc.Editor;
            if (doc == null)
                return;
            if (!blockId.IsNull)
            {
                if (blockId.Database != doc.Database)
                    blockId = ObjectId.Null;
            }
            var (easting, northing, picked) = StreetViewLocate.GetAutoCADPoint();
            if (!picked)
            {
                ed.WriteMessage("\nNo point selected.");
                return;
            }
            int epsgCode = GetCurrentDrawingEPSG();
            if (epsgCode == -1) return;
            (double lat, double lon) = CoordinateConverter.ToWGS84(easting, northing, epsgCode);
            string newUrl =$"https://www.google.com/maps/@{lat},{lon},3a,75y,45h,90t/data=!3m1!1e1";
            StreetViewLocate.DeleteAllStreetViewBlocks();
            blockId = StreetViewLocate.PlaceBlockAtLocation(easting, northing);
            StreetViewLocate.MoveBlock(blockId, easting, northing, 0);
            webView.Source = new Uri(newUrl);
        }
    }
}