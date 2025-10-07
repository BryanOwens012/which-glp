#!/usr/bin/env node

// Test the recommendation flow end-to-end
const testPayload = {
  currentWeight: 200,
  weightUnit: 'lbs',
  goalWeight: 170,
  age: 35,
  sex: 'female',
  hasInsurance: true,
  country: 'USA'
};

async function testRecommendation() {
  try {
    console.log('🧪 Testing recommendation flow...\n');

    // Test ML API directly first
    console.log('1️⃣ Testing ML API directly...');
    const mlResponse = await fetch('http://localhost:8001/api/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testPayload)
    });

    if (!mlResponse.ok) {
      throw new Error(`ML API failed: ${mlResponse.statusText}`);
    }

    const mlResult = await mlResponse.json();
    console.log(`✅ ML API returned ${mlResult.recommendations.length} recommendations`);
    console.log(`   Top recommendation: ${mlResult.recommendations[0]?.drug}\n`);

    // Test through backend
    console.log('2️⃣ Testing through tRPC backend...');
    const backendResponse = await fetch('http://localhost:8000/trpc/recommendations.getForUser', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testPayload)
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      throw new Error(`Backend failed: ${backendResponse.statusText}\n${errorText}`);
    }

    const backendResult = await backendResponse.json();
    console.log('✅ Backend returned successfully');
    console.log(`   Processing time: ${backendResult.result?.data?.processingTime}ms\n`);

    console.log('🎉 End-to-end flow working!');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

testRecommendation();
