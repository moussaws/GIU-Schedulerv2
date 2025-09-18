import React from 'react';
import { Cog6ToothIcon, UserIcon, LockClosedIcon, BellIcon } from '@heroicons/react/24/outline';

const SettingsPage: React.FC = () => {
  return (
    <div className=\"space-y-6\">
      <div>
        <h1 className=\"text-2xl font-bold text-gray-900\">Settings</h1>
        <p className=\"text-gray-600\">Manage your account and system preferences</p>
      </div>

      <div className=\"grid grid-cols-1 lg:grid-cols-2 gap-6\">
        {/* Profile Settings */}
        <div className=\"card\">
          <div className=\"card-header flex items-center space-x-2\">
            <UserIcon className=\"h-5 w-5 text-gray-600\" />
            <span className=\"font-semibold\">Profile Settings</span>
          </div>
          <div className=\"card-body\">
            <div className=\"space-y-4\">
              <div>
                <label className=\"form-label\">Username</label>
                <input type=\"text\" className=\"form-input\" disabled value=\"admin\" />
              </div>
              <div>
                <label className=\"form-label\">Email</label>
                <input type=\"email\" className=\"form-input\" disabled value=\"admin@giu.edu\" />
              </div>
              <div>
                <label className=\"form-label\">Role</label>
                <input type=\"text\" className=\"form-input\" disabled value=\"Administrator\" />
              </div>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className=\"card\">
          <div className=\"card-header flex items-center space-x-2\">
            <LockClosedIcon className=\"h-5 w-5 text-gray-600\" />
            <span className=\"font-semibold\">Security</span>
          </div>
          <div className=\"card-body\">
            <div className=\"space-y-4\">
              <button className=\"w-full btn-secondary text-left\">
                Change Password
              </button>
              <button className=\"w-full btn-secondary text-left\">
                Two-Factor Authentication
              </button>
              <button className=\"w-full btn-secondary text-left\">
                Session Management
              </button>
            </div>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className=\"card\">
          <div className=\"card-header flex items-center space-x-2\">
            <BellIcon className=\"h-5 w-5 text-gray-600\" />
            <span className=\"font-semibold\">Notifications</span>
          </div>
          <div className=\"card-body\">
            <div className=\"space-y-4\">
              <div className=\"flex items-center justify-between\">
                <span className=\"text-sm text-gray-700\">Schedule Generation</span>
                <input type=\"checkbox\" className=\"rounded\" defaultChecked />
              </div>
              <div className=\"flex items-center justify-between\">
                <span className=\"text-sm text-gray-700\">Conflict Alerts</span>
                <input type=\"checkbox\" className=\"rounded\" defaultChecked />
              </div>
              <div className=\"flex items-center justify-between\">
                <span className=\"text-sm text-gray-700\">System Updates</span>
                <input type=\"checkbox\" className=\"rounded\" />
              </div>
            </div>
          </div>
        </div>

        {/* System Preferences */}
        <div className=\"card\">
          <div className=\"card-header flex items-center space-x-2\">
            <Cog6ToothIcon className=\"h-5 w-5 text-gray-600\" />
            <span className=\"font-semibold\">System Preferences</span>
          </div>
          <div className=\"card-body\">
            <div className=\"space-y-4\">
              <div>
                <label className=\"form-label\">Default Policy Set</label>
                <select className=\"form-input\">
                  <option>Standard (Independence OFF)</option>
                  <option>Flexible (Independence ON)</option>
                  <option>Balanced (Equal Count)</option>
                  <option>Strict (Number Matching)</option>
                </select>
              </div>
              <div>
                <label className=\"form-label\">Time Zone</label>
                <select className=\"form-input\">
                  <option>UTC+2 (Cairo)</option>
                  <option>UTC+3 (Kuwait)</option>
                  <option>UTC+0 (GMT)</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className=\"flex justify-end space-x-3\">
        <button className=\"btn-secondary\">Cancel</button>
        <button className=\"btn-primary\">Save Changes</button>
      </div>
    </div>
  );
};

export default SettingsPage;