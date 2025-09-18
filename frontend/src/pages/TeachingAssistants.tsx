import React from 'react';
import { UserGroupIcon, PlusIcon } from '@heroicons/react/24/outline';

const TeachingAssistantsPage: React.FC = () => {
  return (
    <div className=\"space-y-6\">
      <div className=\"flex items-center justify-between\">
        <div>
          <h1 className=\"text-2xl font-bold text-gray-900\">Teaching Assistants</h1>
          <p className=\"text-gray-600\">Manage TAs and their availability</p>
        </div>
        <button className=\"btn-primary flex items-center space-x-2\">
          <PlusIcon className=\"h-5 w-5\" />
          <span>Add TA</span>
        </button>
      </div>

      {/* Coming soon placeholder */}
      <div className=\"card\">
        <div className=\"card-body text-center py-12\">
          <UserGroupIcon className=\"mx-auto h-16 w-16 text-gray-400\" />
          <h3 className=\"mt-4 text-lg font-medium text-gray-900\">TA Management</h3>
          <p className=\"mt-2 text-gray-600\">
            This page is under construction. You'll be able to:
          </p>
          <ul className=\"mt-4 text-sm text-gray-600 space-y-1\">
            <li>• Register new teaching assistants</li>
            <li>• Set maximum weekly hours</li>
            <li>• Configure availability matrix</li>
            <li>• Set slot preferences</li>
            <li>• View workload statistics</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TeachingAssistantsPage;