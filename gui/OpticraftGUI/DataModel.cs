using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.ComponentModel;
using System.IO;
using Nini.Config;
using System.Collections;
using System.Diagnostics;
using System.Reflection;


namespace OpticraftGUI {
    public class DataModel : INotifyPropertyChanged {

        IniConfigSource ConfigSource { get; set; }

        private List<ComboBoxColourItem> _colourComboBoxItems;
        public List<ComboBoxColourItem> ColourComboBoxItems {
            get { return _colourComboBoxItems; }
            private set {
                _colourComboBoxItems = value;
                OnPropertyChanged("ColourComboBoxItems");
            }
        }

        public DataModel() {
            ConfigSource = new IniConfigSource() {
                CaseSensitive = false
            };
            bool unableToLoadFromDisk = !File.Exists("opticraft.ini");
            Exception caughtException = null;

             if (!unableToLoadFromDisk) {
                try {
                    SanitizeConfig("opticraft.ini");
                    ConfigSource.Load("opticraft.ini");
                } catch (Exception e) {
                    caughtException = e;
                    unableToLoadFromDisk = true;
                }
            }
            if (unableToLoadFromDisk) {
                using (StreamReader stream = new StreamReader(Assembly.GetExecutingAssembly().GetManifestResourceStream("OpticraftGUI.Config.opticraft.ini"))) {
                    ConfigSource.Load(stream);
                }
            }

            IsDirty = false;
            PopulateComboBoxItems();
        }
        private void SanitizeConfig(string fileName) {
            File.WriteAllLines(fileName, File.ReadLines(fileName).Where(l => l.Length == 0 || l[0] != '#').ToArray());
        }

        private void PopulateComboBoxItems() {
            ColourComboBoxItems = new List<ComboBoxColourItem>();
            foreach (KeyValuePair<string,string> KVP in ComboBoxColourItem.ColourMappings) {
                ColourComboBoxItems.Add(new ComboBoxColourItem() {
                    ColourString = KVP.Key
                });
            }
            OnPropertyChanged("ColourComboBoxItems");
        }

        public void Save() {
            ConfigSource.Save("opticraft.ini");
            IsDirty = false;
        }

        private bool _isDirty;
        public bool IsDirty {
            get { return _isDirty; }
            set {
                _isDirty = value;
                OnPropertyChanged("IsDirty");
            }
        }
        #region Properties

        #region General Tab

        public string ServerName {
            get { return Get("server", "name", "This server is powered by Opticraft"); }
            set { Set("server", "name", value); }
        }

        public string MOTD {
            get { return Get("server", "motd", "An Opticraft Server"); }
            set { Set("server", "motd", value); }
        }

        public bool Public {
            get { return GetBool("server", "public", true); }
            set { Set("server", "public", value); }
        }

        public int MaxPlayers {
            get { return GetInt("server", "max", 32); }
            set { Set("server", "max", value); }
        }

        public int Port {
            get { return GetInt("server", "port", 25565); }
            set { Set("server", "port", value); }
        }

        //Logging

        public bool LogConsole {
            get { return GetBool("logs", "consolefilelogs", true); }
            set { Set("logs", "consolefilelogs", value); }
        }

        public bool LogCommands {
            get { return GetBool("logs", "commandlogs", true); }
            set { Set("logs", "commandlogs", value); }
        }

        public bool LogChat {
            get { return GetBool("logs", "chatlogs", true); }
            set { Set("logs", "chatlogs", value); }
        }

        public bool ConsoleColour {
            get { return GetBool("server", "consolecolour", true); }
            set { Set("logs", "consolecolour", value); }
        }

        public string LogLevel {
            get {
                int configLevel = GetInt("logs", "consoleloglevel", 0);
                ConsoleLogLevel logLevel = (ConsoleLogLevel)Enum.Parse(typeof(ConsoleLogLevel), configLevel.ToString());
                string s = logLevel.ToString();
                return logLevel.ToString();
            }
            set {
                ConsoleLogLevel logLevel = (ConsoleLogLevel)Enum.Parse(typeof(ConsoleLogLevel), value.ToString(), false);
                Set("logs", "consoleloglevel", (int)logLevel);
            }
        }

        private ComboBoxColourItem _staticColour;
        public ComboBoxColourItem StaticColour {
            get {
                string configColour = Get("server", "staticcolour", "e");
                return ColourComboBoxItems.Where(c => c.ColourCode.Substring(1).ToLower() == configColour.ToLower()).Single();
            }
            set {
                _staticColour = value;
                Set("server", "staticcolour", value.ColourCode.Substring(1));
            }
        }
        private ComboBoxColourItem _valueColour;
        public ComboBoxColourItem ValueColour {
            get {
                string configColour = Get("server", "valuecolour", "e");
                return ColourComboBoxItems.Where(c => c.ColourCode.Substring(1).ToLower() == configColour.ToLower()).Single();
            }
            set {
                _valueColour = value;
                Set("server", "valuecolour", value.ColourCode.Substring(1));
            }
        }
        private ComboBoxColourItem _errorColour;
        public ComboBoxColourItem ErrorColour {
            get {
                string configColour = Get("server", "errorcolour", "e");
                return ColourComboBoxItems.Where(c => c.ColourCode.Substring(1).ToLower() == configColour.ToLower()).Single();
            }
            set {
                _errorColour = value;
                Set("server", "errorcolour", value.ColourCode.Substring(1));
            }
        }
        private ComboBoxColourItem _noticeColour;
        public ComboBoxColourItem NoticeColour {
            get {
                string configColour = Get("server", "noticecolour", "e");
                return ColourComboBoxItems.Where(c => c.ColourCode.Substring(1).ToLower() == configColour.ToLower()).Single();
            }
            set {
                _noticeColour = value;
                Set("server", "noticecolour", value.ColourCode.Substring(1));
            }
        }
        #endregion

        #region Security Tab

        public bool EnableAuthentication {
            get { return !GetBool("server", "lanmode", false); }
            set { 
                Set("server", "lanmode", !value);
                OnPropertyChanged("EnableAuthentication");
            }
        }

        public bool EnableIPFallback {
            get { return GetBool("server", "relaxedauth", false); }
            set { Set("server", "relaxedauth", value); }
        }

        public bool ReuseSalt {
            get { return GetBool("server", "relaxedauth", false); }
            set { Set("server", "relaxedauth", value); }
        }

        public int MaxConnectionsPerIP {
            get { return GetInt("server", "maxconnections", 6); }
            set { Set("server", "maxconnections", value); }
        }

        public bool DisableInsideBot {
            get { return GetBool("server", "disablebots", false); }
            set { Set("server", "disablebots", value); }
        }

        public int ChatLines {
            get { return GetInt("server", "floodlines", 6); }
            set { Set("server", "floodlines", value); }
        }

        public int ChatPeriod {
            get { return GetInt("server", "floodperiod", 5); }
            set { Set("server", "floodperiod", value); }
        }

        public int ChatMute {
            get { return GetInt("server", "floodmute", 10); }
            set { Set("server", "floodmute", value); }
        }

        public int BlockAmount {
            get { return GetInt("server", "blockchangecount", 45); }
            set { Set("server", "blockchangecount", value); }
        }

        public int BlockPeriod {
            get { return GetInt("server", "blockchangeperiod", 5); }
            set { Set("server", "blockchangeperiod", value); }
        }

        public bool DisallowCaps {
            get { return !GetBool("server", "allowcaps", false); }
            set { 
                Set("server", "allowcaps", !value);
                OnPropertyChanged("DisallowCaps");
            }
        }

        public int MinCapsLength {
            get { return GetInt("server", "minlength", 10); }
            set { Set("server", "minlength", value); }
        }

        #endregion

        #region Advanced Tab

        public bool EnableNagleAlgorithm {
            get { return GetBool("server", "lowlatencymode", false); }
            set { Set("server", "lowlatencymode", value); }
        }

        public int ZlibCompressionLevel {
            get { return GetInt("worlds", "compressionlevel", 1); }
            set { Set("worlds", "compressionlevel", value); }
        }

        public int BlockFlushThreshold {
            get { return GetInt("worlds", "logflushthreshold", 10000); }
            set { Set("worlds", "logflushthreshold", value); }
        }     

        #endregion

        #endregion


        #region INotifyPropertyChanged

        public event PropertyChangedEventHandler PropertyChanged;

        public void OnPropertyChanged(string PropertyName) {
            if (PropertyChanged != null) {
                PropertyChanged(this, new PropertyChangedEventArgs(PropertyName));
            }
        }
        #endregion

        #region NiniHelpers

        public string Get(string section, string field, string defaultValue) {
            return ConfigSource.Configs[section].Get(field, defaultValue);
        }

        public int GetInt(string section, string field, int defaultValue) {
            return ConfigSource.Configs[section].GetInt(field, defaultValue);
        }
        
        //Opticraft stores bools as 0 or 1. Nini uses True and False - need to convert.
        public bool GetBool(string section, string field, bool defaultValue) {
            return ConfigSource.Configs[section].GetInt(field, (defaultValue)? 1:0) != 0;
        }

        public double GetDouble(string section, string field, double defaultValue) {
            return ConfigSource.Configs[section].GetDouble(field, defaultValue);
        }

        //Opticraft stores bools as 0 or 1. Nini uses True and False - need to convert.
        public void Set(string section, string field, object value) {

            if (value is bool) {
                value = (bool)value ? 1 : 0;
            }
            ConfigSource.Configs[section].Set(field, value);
            IsDirty = true;
        }

        #endregion

    }
}
