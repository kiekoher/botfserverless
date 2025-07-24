import { strict as assert } from 'assert';
import sinon from 'sinon';
import esmock from 'esmock';

const importClassifier = async (textFn) => {
  const modelStub = { generateContent: sinon.stub().resolves({ response: { text: textFn } }) };
  const GoogleGenerativeAIStub = sinon.stub().returns({ getGenerativeModel: () => modelStub });

  const { classifyAndExtract } = await esmock('../src/services/geminiClassifier.js', {
    '@google/generative-ai': { GoogleGenerativeAI: GoogleGenerativeAIStub }
  });
  return classifyAndExtract;
};

describe('geminiClassifier.classifyAndExtract', () => {
  it('parses JSON embedded in response', async () => {
    const decision = { decision: 'clarify', tool_call: null, summary_for_rag: 'hola' };
    const textFn = () => `some text\n${JSON.stringify(decision)}\nextra`;
    const classifyAndExtract = await importClassifier(textFn);

    const res = await classifyAndExtract('hola');
    assert.deepEqual(res, decision);
  });

  it('returns default decision when output lacks JSON', async () => {
    const classifyAndExtract = await importClassifier(() => 'no json here');
    const res = await classifyAndExtract('test');
    assert.deepEqual(res, { decision: 'use_rag', tool_call: null, summary_for_rag: 'test' });
  });
});
