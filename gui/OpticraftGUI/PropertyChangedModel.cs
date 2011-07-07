using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.ComponentModel;

namespace OpticraftGUI {
    public class PropertyChangedModel : INotifyPropertyChanged {

        private Dictionary<string, object> ItemStore = new Dictionary<string, object>();
        public event PropertyChangedEventHandler PropertyChanged;

        public void Set(string field, object value) {
            ItemStore[field] = value;
            OnPropertyChanged(field);
        }

        public T Get<T>(string field) {
            object result;
            return ItemStore.TryGetValue(field, out result) ? (T)result : default(T);
        }

        public void OnPropertyChanged(string propertyName) {
            if (PropertyChanged != null) {
                PropertyChanged(this, new PropertyChangedEventArgs(propertyName));
            }
        }

    }
}
