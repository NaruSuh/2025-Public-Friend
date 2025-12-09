import { PrismaClient, AuthType, ResponseFormat } from '@prisma/client';

const prisma = new PrismaClient();

const apiSources = [
  {
    name: 'nabostats',
    displayName: '재정경제통계시스템',
    baseUrl: 'https://www.nabostats.go.kr',
    authType: AuthType.API_KEY,
    authConfig: {
      keyParamName: 'serviceKey',
      keyLocation: 'query',
    },
    responseFormat: ResponseFormat.JSON,
    isActive: true,
  },
  {
    name: 'nec_manifesto',
    displayName: '중앙선거관리위원회 선거공약',
    baseUrl: 'https://www.data.go.kr',
    authType: AuthType.API_KEY,
    authConfig: {
      keyParamName: 'serviceKey',
      keyLocation: 'query',
    },
    responseFormat: ResponseFormat.JSON,
    isActive: true,
  },
  {
    name: 'rone',
    displayName: '부동산통계정보 R-ONE',
    baseUrl: 'https://www.reb.or.kr/r-one',
    authType: AuthType.API_KEY,
    authConfig: {
      keyParamName: 'serviceKey',
      keyLocation: 'query',
    },
    responseFormat: ResponseFormat.JSON,
    isActive: true,
  },
  {
    name: 'youtube',
    displayName: 'YouTube Data API',
    baseUrl: 'https://www.googleapis.com/youtube/v3',
    authType: AuthType.API_KEY,
    authConfig: {
      keyParamName: 'key',
      keyLocation: 'query',
    },
    responseFormat: ResponseFormat.JSON,
    isActive: true,
  },
];

async function main() {
  console.log('Seeding API sources...');

  for (const source of apiSources) {
    const result = await prisma.apiSource.upsert({
      where: { name: source.name },
      update: source,
      create: source,
    });
    console.log(`✓ ${result.displayName} (${result.name})`);
  }

  // Add API keys from environment
  const env = process.env;
  const apiKeys = [
    {
      sourceName: 'nabostats',
      keyValue: env.NABOSTATS_API_KEY || '',
      label: 'Default Key',
    },
    {
      sourceName: 'nec_manifesto',
      keyValue: env.NEC_MANIFESTO_API_KEY || '',
      label: 'Default Key',
    },
    {
      sourceName: 'rone',
      keyValue: env.RONE_API_KEY || '',
      label: 'Default Key',
    },
    {
      sourceName: 'youtube',
      keyValue: env.YOUTUBE_API_KEY || '',
      label: 'Default Key',
    },
  ];

  console.log('\nAdding API keys...');
  for (const key of apiKeys) {
    if (!key.keyValue) continue;

    const source = await prisma.apiSource.findUnique({
      where: { name: key.sourceName },
    });

    if (source) {
      const existing = await prisma.apiKey.findFirst({
        where: {
          sourceId: source.id,
          label: key.label,
        },
      });

      if (!existing) {
        await prisma.apiKey.create({
          data: {
            sourceId: source.id,
            keyValue: key.keyValue,
            label: key.label,
            isActive: true,
          },
        });
        console.log(`✓ Added key for ${source.displayName}`);
      } else {
        console.log(`  Key already exists for ${source.displayName}`);
      }
    }
  }

  console.log('\nDone!');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
