import React, { useEffect, useState } from 'react';
import { Settings, Shield } from 'lucide-react';
import axios from 'axios';
import { User } from '../../types';

interface SettingsData {
  [key: string]: string | boolean;
}

export default function SettingsPage({ user }: { user: User }) {
  const [settings, setSettings] = useState<SettingsData>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/settings');
      setSettings(response.data.settings || {});
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post('/api/settings', settings);
      alert('Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  const toggleSetting = (key: string, value: boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const updateSetting = (key: string, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const settingRows = [
    {
      title: 'Dark Mode',
      description: 'Enable dark theme for the application',
      key: 'dark_mode',
      type: 'toggle',
    },
    {
      title: 'Email Notifications',
      description: 'Receive email updates for review cycles and assessments',
      key: 'email_notifications',
      type: 'toggle',
    },
    {
      title: 'Auto-save Drafts',
      description: 'Automatically save assessment drafts',
      key: 'auto_save',
      type: 'toggle',
    },
    {
      title: 'Show Performance Trends',
      description: 'Display trend indicators in dashboards',
      key: 'show_trends',
      type: 'toggle',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Configure application preferences</p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5 text-teal-600" />
              Application Settings
            </h2>
            <div className="space-y-4">
              {settingRows.map((item) => (
                <div key={item.key} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <h3 className="font-medium text-slate-900">{item.title}</h3>
                    <p className="text-sm text-slate-500">{item.description}</p>
                  </div>
                  <label className="relative inline-flex h-6 w-11 items-center rounded-full border border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2">
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={!!settings[item.key]}
                      onChange={(e) => toggleSetting(item.key, e.target.checked)}
                    />
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full shadow transition-transform ${
                        !!settings[item.key]
                          ? 'bg-teal-500'
                          : 'bg-slate-200'
                      }`}
                    />
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-teal-600" />
              Account Settings
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Display Name</label>
                <input
                  type="text"
                  value={user.full_name}
                  onChange={(e) => updateSetting('display_name', e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email Notifications Address</label>
                <input
                  type="email"
                  value={user.email}
                  onChange={(e) => updateSetting('notification_email', e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-teal-600 text-white rounded-xl hover:bg-teal-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}