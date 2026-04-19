import aiohttp
import asyncio
import json

async def test():
    # Public server (e.g. some popular Rust server)
    # Rustoria EU Main BM ID: 9546059
    # A random player BM ID: 1234567
    
    server_id = '9546059'
    steam_id = '76561198031548652' # some steam id, hopefully has BM
    
    async with aiohttp.ClientSession() as session:
        # Search player by steam id
        url = f"https://api.battlemetrics.com/players?filter[search]={steam_id}&filter[game]=rust"
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get('data'):
                player_id = data['data'][0]['id']
                print(f"Found player ID: {player_id}")
                
                # Get server specific info
                url2 = f"https://api.battlemetrics.com/players/{player_id}/servers/{server_id}"
                async with session.get(url2) as resp2:
                    data2 = await resp2.json()
                    print(json.dumps(data2, indent=2))
            else:
                print("Player not found")

if __name__ == '__main__':
    asyncio.run(test())
