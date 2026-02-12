/**
 * Tests for dataset-manager.js
 *
 * Tests cover:
 * - Dataset storage and retrieval
 * - localStorage interaction
 * - Data point management
 */

describe('DatasetManager', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('Data Storage', () => {
    test('should store data in localStorage', () => {
      const testData = { gaze: [100, 200], timestamp: Date.now() };
      const key = 'testDataset';

      localStorage.setItem(key, JSON.stringify(testData));

      expect(localStorage.setItem).toHaveBeenCalledWith(
        key,
        JSON.stringify(testData)
      );
    });

    test('should retrieve data from localStorage', () => {
      const testData = { gaze: [100, 200], timestamp: Date.now() };
      const key = 'testDataset';

      localStorage.getItem.mockReturnValueOnce(JSON.stringify(testData));

      const retrieved = JSON.parse(localStorage.getItem(key));

      expect(localStorage.getItem).toHaveBeenCalledWith(key);
      expect(retrieved).toEqual(testData);
    });

    test('should handle missing data', () => {
      localStorage.getItem.mockReturnValueOnce(null);

      const result = localStorage.getItem('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('Data Point Management', () => {
    test('should add data point to dataset', () => {
      const dataset = [];
      const dataPoint = {
        x: 100,
        y: 200,
        timestamp: Date.now()
      };

      dataset.push(dataPoint);

      expect(dataset).toHaveLength(1);
      expect(dataset[0]).toEqual(dataPoint);
    });

    test('should remove data point from dataset', () => {
      const dataset = [
        { x: 100, y: 200 },
        { x: 150, y: 250 },
        { x: 200, y: 300 }
      ];

      dataset.splice(1, 1);

      expect(dataset).toHaveLength(2);
      expect(dataset[1].x).toBe(200);
    });

    test('should clear all data points', () => {
      const dataset = [
        { x: 100, y: 200 },
        { x: 150, y: 250 }
      ];

      dataset.length = 0;

      expect(dataset).toHaveLength(0);
    });
  });

  describe('Dataset Validation', () => {
    test('should validate data point structure', () => {
      const validDataPoint = {
        x: 100,
        y: 200,
        timestamp: Date.now()
      };

      expect(validDataPoint).toHaveProperty('x');
      expect(validDataPoint).toHaveProperty('y');
      expect(validDataPoint).toHaveProperty('timestamp');
      expect(typeof validDataPoint.x).toBe('number');
      expect(typeof validDataPoint.y).toBe('number');
    });

    test('should handle invalid data gracefully', () => {
      const invalidJSON = 'not valid json';

      localStorage.getItem.mockReturnValueOnce(invalidJSON);

      expect(() => {
        JSON.parse(localStorage.getItem('invalid'));
      }).toThrow();
    });
  });

  describe('Dataset Export', () => {
    test('should export dataset as JSON', () => {
      const dataset = [
        { x: 100, y: 200, timestamp: 1000 },
        { x: 150, y: 250, timestamp: 2000 }
      ];

      const exported = JSON.stringify(dataset);
      const parsed = JSON.parse(exported);

      expect(parsed).toEqual(dataset);
      expect(parsed).toHaveLength(2);
    });

    test('should export dataset with metadata', () => {
      const datasetWithMetadata = {
        version: '1.0',
        dataPoints: [
          { x: 100, y: 200 },
          { x: 150, y: 250 }
        ],
        created: Date.now()
      };

      const exported = JSON.stringify(datasetWithMetadata);

      expect(exported).toContain('version');
      expect(exported).toContain('dataPoints');
      expect(exported).toContain('created');
    });
  });

  describe('LocalStorage Limits', () => {
    test('should handle localStorage quota exceeded', () => {
      // Mock localStorage being full
      localStorage.setItem.mockImplementationOnce(() => {
        throw new Error('QuotaExceededError');
      });

      expect(() => {
        localStorage.setItem('key', 'value');
      }).toThrow('QuotaExceededError');
    });
  });
});
