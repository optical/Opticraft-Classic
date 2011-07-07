using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OpticraftGUI {
    public class ComboBoxColourItem {
        public string ColourString { get; set; }
        public static Dictionary<string, string> ColourMappings = new Dictionary<string, string>() {
            {"Black", "0"},
            {"Dark Blue", "1"},
            {"Dark Green", "2"},
            {"Dark Teal", "3"},
            {"Dark Red", "4"},
            {"Purple", "5"},
            {"Gold", "6"},
            {"Grey", "7"},
            {"Dark Grey", "8"},
            {"Blue", "9"},
            {"Bright Green", "a"},
            {"Teal", "b"},
            {"Red", "c"},
            {"Pink", "d"},
            {"Yellow", "e"},
            {"White", "f"},
        };
        public string ColourCode { get { return '&' + ColourMappings[ColourString]; } }
        public override string ToString() {
            return ColourString;
        }
    }
}
