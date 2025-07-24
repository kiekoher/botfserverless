import { strict as assert } from 'assert';
import sinon from 'sinon';
import esmock from 'esmock';

const BOT_PERSONA = 'PERSONA';

const createService = async (rpcResult, generateText = 'resp') => {
  const embedModel = { embedContent: sinon.stub().resolves({ embedding: { values: [0.1, 0.2] } }) };
  const genModel = { generateContent: sinon.stub().resolves({ response: { text: () => generateText } }) };
  const GoogleGenerativeAIStub = sinon.stub().returns({
    getGenerativeModel: sinon.stub()
      .onFirstCall().returns(embedModel)
      .onSecondCall().returns(genModel)
  });

  process.env.SUPABASE_URL = 'http://test';
  process.env.SUPABASE_KEY = 'testkey';

  const { processRagQuery } = await esmock(
    '../src/services/ragGeminiService.js',
    import.meta.url,
    {
      '@google/generative-ai': { GoogleGenerativeAI: GoogleGenerativeAIStub }
    }
  );
  const { supabase } = await import('../src/services/supabaseClient.js');
  const sandbox = sinon.createSandbox();
  const rpcStub = sandbox.stub(supabase, 'rpc').resolves(rpcResult);

  return { processRagQuery, rpcStub, genModel, sandbox };
};

describe('ragGeminiService.processRagQuery', () => {
  it('returns response without context when RPC fails or returns no chunks', async () => {
    const { processRagQuery, rpcStub, genModel, sandbox } = await createService({ data: null, error: new Error('fail') }, 'sin');
    const result = await processRagQuery('hola', [{ sender: 'Usuario', message: 'h' }]);
    assert.equal(result.response, 'sin');
    assert.deepEqual(result.context, []);
    assert.ok(rpcStub.calledOnce);
    assert.ok(genModel.generateContent.calledOnce);
    sandbox.restore();
  });

  it('returns response and context when RPC provides chunks', async () => {
    const chunks = [{ content_text: 'uno' }, { content_text: 'dos' }];
    const { processRagQuery, rpcStub, genModel, sandbox } = await createService({ data: chunks, error: null }, 'con');
    const result = await processRagQuery('hola', []);
    assert.equal(result.response, 'con');
    assert.deepEqual(result.context, ['uno', 'dos']);
    const prompt = genModel.generateContent.firstCall.args[0];
    assert.ok(prompt.includes('uno'));
    assert.ok(prompt.includes('dos'));
    assert.ok(rpcStub.calledOnce);
    sandbox.restore();
  });
});
