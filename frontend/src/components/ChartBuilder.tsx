import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { eventTracker } from '../services/eventTracker';

interface ChartBuilderProps {
  rows: Array<Record<string, any>>;
  columnNames: string[];
  onClose: () => void;
}

type ChartType = 'bar' | 'line' | 'pie';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

const ChartBuilder: React.FC<ChartBuilderProps> = ({ rows, columnNames, onClose }) => {
  const [chartType, setChartType] = useState<ChartType>('bar');
  const [xColumn, setXColumn] = useState<string>(columnNames[0] || '');
  const [yColumns, setYColumns] = useState<string[]>([columnNames[1] || '']);
  const [showChart, setShowChart] = useState(false);

  const handleCreateChart = () => {
    // Validate that at least one Y column is selected
    if (yColumns.length === 0) {
      alert('Please select at least one Y-axis column');
      return;
    }
    
    setShowChart(true);
    
    // Log chart creation event
    eventTracker.trackEvent('CHART_CREATED', {
      chart_type: chartType,
      x_column: xColumn,
      y_columns: yColumns,
      row_count: rows.length,
    });
  };

  const toggleYColumn = (col: string) => {
    if (chartType === 'pie') {
      // Pie charts only support one Y column
      setYColumns([col]);
    } else {
      setYColumns(prev => 
        prev.includes(col) 
          ? prev.filter(c => c !== col)
          : [...prev, col]
      );
    }
  };

  const prepareChartData = () => {
    return rows.map((row) => {
      const dataPoint: Record<string, any> = {
        [xColumn]: String(row[xColumn]),
      };
      yColumns.forEach(yCol => {
        dataPoint[yCol] = parseFloat(String(row[yCol])) || 0;
      });
      return dataPoint;
    });
  };

  const renderChart = () => {
    const data = prepareChartData();

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xColumn} />
              <YAxis />
              <Tooltip />
              <Legend />
              {yColumns.map((yCol, index) => (
                <Bar key={yCol} dataKey={yCol} fill={COLORS[index % COLORS.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xColumn} />
              <YAxis />
              <Tooltip />
              <Legend />
              {yColumns.map((yCol, index) => (
                <Line 
                  key={yCol} 
                  type="monotone" 
                  dataKey={yCol} 
                  stroke={COLORS[index % COLORS.length]} 
                  strokeWidth={2} 
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={data}
                dataKey={yColumns[0]}
                nameKey={xColumn}
                cx="50%"
                cy="50%"
                outerRadius={120}
                label
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="mt-4 p-4 border border-gray-300 rounded-lg bg-white">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">📊 Chart Builder</h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 text-sm font-medium"
        >
          ✕ Close
        </button>
      </div>

      {!showChart ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chart Type
            </label>
            <div className="flex gap-2">
              {(['bar', 'line', 'pie'] as ChartType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setChartType(type)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    chartType === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              X-Axis (Category)
            </label>
            <select
              value={xColumn}
              onChange={(e) => setXColumn(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {columnNames.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Y-Axis (Value{chartType !== 'pie' ? 's' : ''})
              {chartType !== 'pie' && <span className="text-xs text-gray-500 ml-2">(Select multiple)</span>}
            </label>
            <div className="border border-gray-300 rounded-md p-3 max-h-48 overflow-y-auto">
              {columnNames.map((col) => (
                <label key={col} className="flex items-center space-x-2 mb-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                  <input
                    type={chartType === 'pie' ? 'radio' : 'checkbox'}
                    name={chartType === 'pie' ? 'y-axis-pie' : undefined}
                    checked={yColumns.includes(col)}
                    onChange={() => toggleYColumn(col)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{col}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleCreateChart}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors font-medium"
          >
            Create Chart
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4 p-3 bg-blue-50 rounded-md border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>{chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart:</strong> {xColumn} vs {yColumns.join(', ')}
            </p>
          </div>
          {renderChart()}
          <button
            onClick={() => setShowChart(false)}
            className="mt-4 w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
          >
            ← Back to Settings
          </button>
        </div>
      )}
    </div>
  );
};

export default ChartBuilder;
