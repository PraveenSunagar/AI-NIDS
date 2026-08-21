import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty_level"
]

# Attack categories mapping for NSL-KDD
ATTACK_TYPES = {
    "neptune": "DoS", "back": "DoS", "land": "DoS", "pod": "DoS", "smurf": "DoS", "teardrop": "DoS", "mailbomb": "DoS", "apache2": "DoS", "processtable": "DoS", "udpstorm": "DoS",
    "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe", "satan": "Probe", "mscan": "Probe", "saint": "Probe",
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L", "multihop": "R2L", "phf": "R2L", "spy": "R2L", "warezclient": "R2L", "warezmaster": "R2L", "sendmail": "R2L", "named": "R2L", "snmpgetattack": "R2L", "snmpguess": "R2L", "xlock": "R2L", "xsnoop": "R2L", "httptunnel": "R2L",
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R", "rootkit": "U2R", "ps": "U2R", "sqlattack": "U2R", "xterm": "U2R"
}

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

class Preprocessor:
    def __init__(self):
        self.encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_fitted = False

    def load_data(self, file_path):
        """Loads NSL-KDD dataset CSV/txt file without header."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # NSL-KDD txt may have 43 columns (including difficulty_level) or 42
        df = pd.read_csv(file_path, header=None)
        if df.shape[1] == 43:
            df.columns = COLUMN_NAMES
        elif df.shape[1] == 42:
            df.columns = COLUMN_NAMES[:-1]
        else:
            # Fallback if column count varies
            df.columns = COLUMN_NAMES[:df.shape[1]]
        
        # Clean missing & duplicates
        df = df.dropna()
        df = df.drop_duplicates()
        return df

    def transform_labels(self, labels):
        """Transforms labels into binary (NORMAL vs ATTACK) and attack_type."""
        binary_labels = []
        attack_types = []
        for l in labels:
            clean_l = str(l).strip().rstrip('.').lower()
            if clean_l == "normal":
                binary_labels.append("NORMAL")
                attack_types.append("Normal")
            else:
                binary_labels.append("ATTACK")
                attack_types.append(ATTACK_TYPES.get(clean_l, "Other Attack"))
        return np.array(binary_labels), np.array(attack_types)

    def fit_transform(self, df, selected_features=None):
        """Fits encoders and scaler on dataframe and returns processed X and y binary."""
        df_clean = df.copy()
        
        # Handle categorical columns
        for col in CATEGORICAL_COLS:
            if col in df_clean.columns:
                le = LabelEncoder()
                df_clean[col] = le.fit_transform(df_clean[col].astype(str))
                self.encoders[col] = le
        
        y_raw = df_clean["label"].values
        y_binary, y_attack_types = self.transform_labels(y_raw)
        
        X_df = df_clean.drop(columns=["label", "difficulty_level"], errors="ignore")
        
        if selected_features:
            X_df = X_df[selected_features]
        
        self.feature_columns = list(X_df.columns)
        X_scaled = self.scaler.fit_transform(X_df)
        self.is_fitted = True
        
        return X_scaled, y_binary, y_attack_types, X_df

    def transform(self, df_or_dict):
        """Transforms input feature dataframe or dict using fitted encoders and scaler."""
        if not self.is_fitted:
            raise ValueError("Preprocessor is not fitted yet.")
            
        if isinstance(df_or_dict, dict):
            df_input = pd.DataFrame([df_or_dict])
        elif isinstance(df_or_dict, pd.DataFrame):
            df_input = df_or_dict.copy()
        else:
            df_input = pd.DataFrame(df_or_dict)
            
        for col in CATEGORICAL_COLS:
            if col in df_input.columns and col in self.encoders:
                le = self.encoders[col]
                # Handle unseen labels by defaulting to 0 or known classes
                val_str = df_input[col].astype(str)
                df_input[col] = val_str.apply(lambda x: le.transform([x])[0] if x in le.classes_ else 0)
                
        # Filter selected feature columns
        missing_cols = set(self.feature_columns) - set(df_input.columns)
        for col in missing_cols:
            df_input[col] = 0.0
            
        df_input = df_input[self.feature_columns]
        X_scaled = self.scaler.transform(df_input)
        return X_scaled
