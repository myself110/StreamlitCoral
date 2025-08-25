# 🚨 QUICK FIX CARD - Google Drive Access

## ⚡ **IMMEDIATE ACTION REQUIRED**

### **Problem**: Service account exists but cannot access Google Drive
### **Solution**: Add IAM roles in Google Cloud Console

---

## 🔧 **3 Steps to Fix (5 minutes)**

### **Step 1: Go to Google Cloud Console**
- **URL**: [console.cloud.google.com](https://console.cloud.google.com)
- **Project**: `coral-monitoring-467504`
- **Section**: IAM & Admin → IAM

### **Step 2: Find Your Service Account**
- **Look for**: `streamlit@coral-monitoring-467504.iam.gserviceaccount.com`
- **Click**: Pencil/edit icon next to it

### **Step 3: Add These Roles**
- ✅ **Service Account User**
- ✅ **Drive File Stream User**
- ✅ **Project IAM Admin**

---

## 🎯 **What This Fixes**
- ❌ "No folders found" errors
- ❌ "Insufficient authentication scopes" 
- ❌ 404 errors on folder access
- ✅ Full Google Drive access
- ✅ Video streaming working

---

## 🧪 **Test After Fix**
```bash
python test_all_access.py
```
**Expected**: ✅ Found X accessible folders

---

## 📞 **If Still Not Working**
1. **Enable Google Drive API**: APIs & Services → Library → "Google Drive API" → Enable
2. **Share folder**: Right-click folder → Share → Add `streamlit@coral-monitoring-467504.iam.gserviceaccount.com`

---

*Priority: 🔴 CRITICAL - Blocking all functionality*
*Estimated Fix Time: 5 minutes*
