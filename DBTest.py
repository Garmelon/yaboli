import asyncio
import yaboli



class ExampleDB(yaboli.Database):
	@yaboli.Database.operation
	def sample_operation(connection, *args):
		print(args)
		#return a + b
		print("returning 15...")
		return 15

async def run():
	db = ExampleDB("test.db")
	print(db.sample_operation)
	#print(db.sample_operation(1, 2))
	result = await db.sample_operation(1, 2)
	print(result)

def main():
	asyncio.get_event_loop().run_until_complete(run())

if __name__ == "__main__":
	main()
