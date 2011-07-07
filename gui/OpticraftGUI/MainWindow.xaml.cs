using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.ComponentModel;
using Nini.Config;

namespace OpticraftGUI {
    public partial class MainWindow : Window {

        public DataModel ConfigModel { get; set; }

        public MainWindow() {
            ConfigModel = new DataModel();
            this.DataContext = ConfigModel;
            Init();
            InitializeComponent();
        }

        private void Init() {
        }


        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e) {
            Save();
        }

        private void btnSave_Click(object sender, RoutedEventArgs e) {
            Save();
        }

        private void Save() {
            ConfigModel.Save();
        }

        private void btnCancel_Click(object sender, RoutedEventArgs e) {
            Close();
        }

    }
}
