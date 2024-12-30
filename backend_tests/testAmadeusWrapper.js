const { getFlights } = require('../backend/amadeusWrapper');
const fs = require('fs');
const path = require('path');

// Define test cases as separate async functions
const testCases = {
  async case1() {
    console.log('Test Case 1: Valid one-way search');
    const result = await getFlights('ATL', 'LHR', '2025-05-02');
    if (result && result.flights) {
      console.log('Test Case 1 Passed');
      // Save results to JSON file
      const outputPath = path.join(__dirname, 'results', 'test1_results.json');
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
      console.log(`Results saved to ${outputPath}`);
      return true;
    }
    console.error('Test Case 1 Failed: No flights returned');
    return false;
  },

  async case2() {
    console.log('Test Case 2: Invalid number of adults');
    try {
      await getFlights('ATL', 'JFK', '2025-05-01', null, 0);
      console.error('Test Case 2 Failed: Should have thrown an error');
      return false;
    } catch (error) {
      console.log('Test Case 2 Passed:', error.message);
      return true;
    }
  },

  async case3() {
    console.log('Test Case 3: Invalid travel class');
    try {
      await getFlights('ATL', 'JFK', '2025-05-01', null, 1, 'LUXURY');
      console.error('Test Case 3 Failed: Should have thrown an error');
      return false;
    } catch (error) {
      console.log('Test Case 3 Passed:', error.message);
      return true;
    }
  },

  async case4() {
    console.log('Test Case 4: Valid round-trip search');
    const result = await getFlights('ATL', 'CDG', '2025-05-02', '2025-05-10');
    if (result && result.flights) {
      console.log('Test Case 4 Passed');
      // Save results to JSON file
      const outputPath = path.join(__dirname, 'results', 'test4_results.json');
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
      console.log(`Results saved to ${outputPath}`);
      return true;
    }
    console.error('Test Case 4 Failed: No flights returned');
    return false;
  },

  async case5() {
    console.log('Test Case 5: Missing required fields');
    try {
      await getFlights();
      console.error('Test Case 5 Failed: Should have thrown an error');
      return false;
    } catch (error) {
      console.log('Test Case 5 Passed:', error.message);
      return true;
    }
  }
};

async function runTests(selectedTests = []) {
  console.log('Running selected test cases...\n');
  
  try {
    // If no tests specified, run all tests
    const testsToRun = selectedTests.length > 0 ? selectedTests : Object.keys(testCases);
    
    for (const testName of testsToRun) {
      if (testCases[testName]) {
        console.log(`\nExecuting ${testName}...`);
        try {
          await testCases[testName]();
        } catch (error) {
          console.error(`${testName} failed with error:`, error.message);
        }
      } else {
        console.error(`Test case "${testName}" not found`);
      }
    }
  } catch (error) {
    console.error('Test execution failed:', error);
  }
  
  console.log('\nTests complete.');
}

// Get command line arguments, skipping node and script name
const args = process.argv.slice(2);

// Run specific tests if provided, otherwise run all tests
runTests(args.length > 0 ? args : []);
