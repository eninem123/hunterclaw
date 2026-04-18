#!/usr/bin/env node
/**
 * GBrain Embedding Proxy
 * 监听 localhost:18881，接收 OpenAI 格式的 embedding 请求
 * 转发给 GLM API (embedding-2, 1024维)
 * GLM 的 key 从 /home/lighthouse/.env 读取
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 18881;
const GLM_KEY = fs.readFileSync('/home/lighthouse/.env', 'utf8')
  .match(/glmkey=(.+)/)?.[1]?.trim() || '';
const GLM_URL = 'https://open.bigmodel.cn/api/paas/v4/embeddings';

const server = http.createServer(async (req, res) => {
  if (req.method !== 'POST' || !req.url.includes('/embeddings')) {
    res.writeHead(404);
    res.end('not found');
    return;
  }

  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', async () => {
    try {
      const parsed = JSON.parse(body);
      // 提取 input（支持批量）
      const inputs = Array.isArray(parsed.input) ? parsed.input : [parsed.input];
      const model = parsed.model || 'text-embedding-3-large';

      // GLM API 格式
      const glmPayload = {
        model: 'embedding-2',
        input: inputs,
      };

      // 转发给 GLM
      const glmRes = await fetch(GLM_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${GLM_KEY}`,
        },
        body: JSON.stringify(glmPayload),
      });

      const glmData = await glmRes.json();
      
      // 转换回 OpenAI 格式
      const openaiResponse = {
        object: 'list',
        data: glmData.data.map((item, i) => ({
          object: 'embedding',
          embedding: item.embedding,
          index: i,
        })),
        model: model,
        usage: {
          prompt_tokens: glmData.usage?.prompt_tokens || 0,
          total_tokens: glmData.usage?.total_tokens || 0,
        },
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(openaiResponse));
    } catch (e) {
      res.writeHead(500);
      res.end(JSON.stringify({ error: e.message }));
    }
  });
});

server.listen(PORT, () => {
  console.log(`GBrain Embedding Proxy running at http://localhost:${PORT}`);
  console.log(`GLM Key: ${GLM_KEY ? 'OK' : 'MISSING'}`);
});
