# 🚨 Google Drive Video Streamer - Troubleshooting Notes

## 📋 **Current Status Summary**
- **Project**: Coral Monitoring Streamlit Dashboard
- **Goal**: Stream videos from Google Drive using service account authentication
- **Current Issue**: Service account exists but has insufficient permissions to access Google Drive
- **Last Test**: `test_all_access.py` confirmed no access to any folders

---

## 🔍 **Problem Diagnosis**

### **Root Cause Identified**
The service account `streamlit@coral-monitoring-467504.iam.gserviceaccount.com` **exists and can authenticate** but lacks the necessary **IAM roles** to access Google Drive API.

### **Evidence from Tests**
1. **`test_all_access.py`**: ❌ No folders found - service account has no access to any folders
2. **`list_service_accounts.py`**: ❌ Insufficient authentication scopes for IAM operations
3. **`debug_folder_access.py`**: ❌ 404 errors when trying to access specific folder IDs

---

## ⚠️ **Future Compatibility Warnings**

### **Pandas Frequency Deprecation Warning**
**File**: `fish_tank_dashboard.py` (line 82)
**Warning**: `FutureWarning: 'H' is deprecated and will be removed in a future version, please use 'h' instead.`

**Code causing issue**:
```python
dates = pd.date_range(start='2025-01-15', end='2025-01-21', freq='H')
```

**Fix Required**:
```python
# Change from:
dates = pd.date_range(start='2025-01-15', end='2025-01-21', freq='H')

# To:
dates = pd.date_range(start='2025-01-15', end='2025-01-21', freq='h')
```

**Impact**: 
- Currently works but will break in future pandas versions
- Affects the complex dashboard (`fish_tank_dashboard.py`)
- Simple UI (`simple_fish_tank_ui.py`) is not affected

**Action Required**: Update frequency parameter from `'H'` to `'h'` before future pandas updates

---

## 🛠️ **Required Fixes**

### **1. IAM Role Assignment (CRITICAL)**
**Location**: Google Cloud Console → IAM & Admin → IAM
**Service Account**: `streamlit@coral-monitoring-467504.iam.gserviceaccount.com`

**Required Roles**:
- ✅ **Service Account User** (basic access)
- ✅ **Drive File Stream User** (Google Drive access)
- ✅ **Project IAM Admin** (manage other service accounts)

### **2. Google Drive API Enablement**
**Location**: Google Cloud Console → APIs & Services → Library
**Action**: Search for "Google Drive API" → Enable

### **3. Folder Sharing (After API is enabled)**
**Location**: Google Drive → Right-click folder → Share
**Share with**: `streamlit@coral-monitoring-467504.iam.gserviceaccount.com`
**Permission**: Content Manager

---

## 📁 **Current File Structure**

### **Main Application**
- `gdrive_video_streamer.py` - Main Streamlit app (currently non-functional due to permissions)
- `simple_fish_tank_ui.py` - Simple UI matching image design (working)
- `fish_tank_dashboard.py` - Complex dashboard with charts (has deprecation warning)
- `requirements.txt` - Dependencies
- `README.md` - Setup instructions

### **Debug Scripts Created**
- `debug_folder_access.py` - Tests specific folder access
- `check_root.py` - Tests root folder access
- `find_accessible_folders.py` - Lists all accessible folders
- `test_specific_folder.py` - Tests specific folder with error diagnosis
- `test_all_access.py` - Comprehensive access test
- `list_service_accounts.py` - Lists available service accounts

---

## 🔧 **Technical Details**

### **Service Account Information**
- **Email**: `streamlit@coral-monitoring-467504.iam.gserviceaccount.com`
- **Project ID**: `coral-monitoring-467504`
- **Status**: ✅ Exists, ✅ Can authenticate, ❌ No Drive access

### **Current FOLDER_ID**
```python
FOLDER_ID = "1El_4oQgrz0KeI6mulM9Lu5lPP0IlHwITE"
```
**Note**: This ID is confirmed correct by user, but service account cannot access it.

### **Authentication Method**
- **Type**: Service Account (JSON key file)
- **File**: `service_account.json`
- **Scopes**: `https://www.googleapis.com/auth/drive.readonly`

---

## 📊 **Test Results Summary**

| Test Script | Status | Result |
|-------------|--------|---------|
| `test_all_access.py` | ❌ Failed | No folders accessible |
| `list_service_accounts.py` | ❌ Failed | Insufficient IAM scopes |
| `debug_folder_access.py` | ❌ Failed | 404 errors on folder access |
| `check_root.py` | ❌ Failed | Root folder inaccessible |
| `find_accessible_folders.py` | ❌ Failed | No folders found |

---

## 🚀 **Next Steps After Fix**

### **1. Test Basic Access**
```bash
python test_all_access.py
```
**Expected**: Should show accessible folders and root access

### **2. Test Specific Folder**
```bash
python test_specific_folder.py
```
**Expected**: Should successfully access the target folder

### **3. Run Main Application**
```bash
streamlit run gdrive_video_streamer.py
```
**Expected**: Should find videos and display them in Streamlit

---

## ⚠️ **Common Mistakes to Avoid**

1. **Don't skip IAM role assignment** - Service accounts need explicit permissions
2. **Don't forget to enable Google Drive API** - Authentication alone isn't enough
3. **Don't assume folder sharing is automatic** - Must explicitly share with service account email
4. **Don't use OAuth2 for production** - Service accounts are more reliable
5. **Don't ignore deprecation warnings** - Update pandas frequency from 'H' to 'h'

---

## 🔗 **Useful Resources**

- [Google Cloud IAM Documentation](https://cloud.google.com/iam/docs)
- [Google Drive API Setup](https://developers.google.com/drive/api/guides/enable-drive-api)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/service-accounts)
- [Google Drive Sharing Permissions](https://support.google.com/drive/answer/2494886)
- [Pandas Date Range Frequency](https://pandas.pydata.org/docs/reference/api/pandas.date_range.html)

---

## 📝 **Notes for Future Reference**

- **Created**: [Current Date]
- **Issue Type**: Service Account Permission Configuration
- **Resolution Status**: Pending IAM role assignment
- **Priority**: HIGH - Blocking core functionality
- **Estimated Fix Time**: 15-30 minutes (once in Google Cloud Console)
- **Future Issues**: Pandas frequency deprecation warning needs fixing

---

## 🎯 **Success Criteria**

The application will be considered **FIXED** when:
1. ✅ `test_all_access.py` shows accessible folders
2. ✅ `test_specific_folder.py` can access the target folder
3. ✅ Streamlit app can find and display videos
4. ✅ Video streaming works without authentication errors
5. ✅ Pandas deprecation warning is resolved

---

*Last Updated: [Current Date]*
*Status: 🔴 BLOCKED - Awaiting IAM Configuration*
*Future Issues: ⚠️ Pandas frequency deprecation warning*
